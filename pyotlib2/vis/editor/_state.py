"""EditorState: pure-Python logic for the interactive editor.

No PySide6 imports — fully testable without a display.

Coordinate system
-----------------
Points are stored as integer (x, y) on a logical grid [0, GRID_MAX]².
Y axis: math convention (y increases upward).

The GUI maps this grid to screen pixels via a QTransform.  No float
rounding is ever applied to the stored coordinates — OT is computed
directly from integer coords, so loading a file and displaying it in the
editor can never corrupt the order type.

If the user drags a point, the new position is rounded to the nearest
integer before being stored.
"""

from __future__ import annotations

import time
from typing import Callable, Optional

GRID_MAX = 10000   # logical coordinate range [0, GRID_MAX]


class EditorState:
    """Mutable editor state, independent of the GUI.

    Parameters
    ----------
    pts :
        Initial point positions as integer (x, y) pairs in [0, GRID_MAX]².
    on_ot_changed :
        Callback(changed: bool) fired when OT status flips.
    on_collinear_changed :
        Callback(collinear_triples: list[tuple[int,int,int]]) fired when
        collinearity status changes.
    """

    def __init__(
        self,
        pts: list[tuple[int, int]],
        on_ot_changed: Optional[Callable[[bool], None]] = None,
        on_collinear_changed: Optional[Callable[[list], None]] = None,
    ):
        self._coords: list[list[int]] = [[int(x), int(y)] for x, y in pts]
        self._on_ot_changed = on_ot_changed or (lambda _: None)
        self._on_collinear_changed = on_collinear_changed or (lambda _: None)

        self._orig_ot_key: Optional[bytes] = None
        self._ot_changed = False
        self._collinear_triples: list[tuple[int, int, int]] = []

        self._orig_ot_key = self._compute_ot_key()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def n(self) -> int:
        return len(self._coords)

    def get_coords(self) -> list[tuple[int, int]]:
        """Return current integer (x, y) positions."""
        return [(c[0], c[1]) for c in self._coords]

    def move_point(self, index: int, x: int, y: int) -> None:
        """Move point *index* to integer position (x, y) and update state."""
        if index < 0 or index >= self.n:
            raise IndexError(f"point index {index} out of range [0, {self.n})")
        self._coords[index][0] = int(round(x))
        self._coords[index][1] = int(round(y))
        self._recompute()

    def get_hull_indices(self) -> list[int]:
        """Return convex hull point indices (unsorted). Empty if collinear."""
        sl = self._get_small_lambda_internal()
        if sl is None:
            return []
        try:
            return sl.get_extremal_points()
        except Exception:
            return []

    def get_onion_layers(self) -> list[list[int]]:
        """Return convex layers (onion peeling). Each layer is a list of indices."""
        remaining = list(range(self.n))
        layers = []
        coords = self.get_coords()
        while len(remaining) >= 3:
            pts = [coords[i] for i in remaining]
            try:
                from pyotlib2.core.point_set import PointSet
                ps = PointSet(len(pts), pts)
                sl = ps.to_small_lambda(lazy=False)
                hull_local = sl.get_extremal_points()
                hull_global = [remaining[i] for i in hull_local]
                layers.append(hull_global)
                remaining = [i for i in remaining if i not in hull_global]
            except Exception:
                break
        if remaining:
            layers.append(remaining)
        return layers

    @property
    def ot_changed(self) -> bool:
        return self._ot_changed

    @property
    def collinear_triples(self) -> list[tuple[int, int, int]]:
        return list(self._collinear_triples)

    @property
    def has_collinear(self) -> bool:
        return len(self._collinear_triples) > 0

    def would_change_ot(self, index: int, x: int, y: int) -> bool:
        """Check if moving point *index* to (x,y) would change the OT.
        Does NOT modify state.
        """
        old = (self._coords[index][0], self._coords[index][1])
        self._coords[index][0] = int(round(x))
        self._coords[index][1] = int(round(y))
        key = self._compute_ot_key()
        self._coords[index][0] = old[0]
        self._coords[index][1] = old[1]
        if key is None or self._orig_ot_key is None:
            return True
        return key != self._orig_ot_key

    def lock_current_ot(self) -> None:
        """Set the current OT as the new reference."""
        self._orig_ot_key = self._compute_ot_key()
        if self._ot_changed:
            self._ot_changed = False
            self._on_ot_changed(False)

    def get_small_lambda(self):
        """Return current SmallLambda, or None if collinear/invalid."""
        if self.has_collinear:
            return None
        return self._get_small_lambda_internal()

    def compute_property(self, name: str) -> tuple:
        """Compute a named property. Returns (value, elapsed_seconds).

        value is an int or '—' on failure.
        """
        sl = self.get_small_lambda()
        if sl is None:
            return ("—", 0.0)
        t0 = time.perf_counter()
        try:
            val = _compute_prop(sl, name)
        except Exception as e:
            val = f"err"
        elapsed = time.perf_counter() - t0
        return (val, elapsed)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _get_small_lambda_internal(self):
        try:
            from pyotlib2.core.point_set import PointSet
            ps = PointSet(self.n, self.get_coords())
            return ps.to_small_lambda(lazy=False)
        except Exception:
            return None

    def _compute_ot_key(self) -> Optional[bytes]:
        """Chirotope fingerprint via PointSet.orientation(). None if collinear."""
        try:
            from pyotlib2.core.point_set import PointSet
            ps = PointSet(self.n, self.get_coords())
            n = self.n
            triples = []
            collinear = []
            for a in range(n):
                for b in range(a + 1, n):
                    for c in range(b + 1, n):
                        v = ps.orientation(a, b, c)
                        if v == 0:
                            collinear.append((a, b, c))
                        triples.append(1 if v > 0 else 0)
            # update collinearity (don't fire callback here — called from _recompute)
            self._collinear_triples = collinear
            if collinear:
                return None
            return bytes(triples)
        except Exception:
            return None

    def _recompute(self) -> None:
        old_collinear = list(self._collinear_triples)
        key = self._compute_ot_key()
        new_collinear = list(self._collinear_triples)

        # fire collinear callback if changed
        if new_collinear != old_collinear:
            self._on_collinear_changed(new_collinear)

        changed = (key != self._orig_ot_key) if (
            self._orig_ot_key is not None and key is not None
        ) else False
        if changed != self._ot_changed:
            self._ot_changed = changed
            self._on_ot_changed(changed)


# ------------------------------------------------------------------
# Property registry
# ------------------------------------------------------------------

# Each entry: (display_name, internal_key)
ALL_PROPERTIES: list[tuple[str, str]] = [
    ("Hull size",       "hull"),
    ("Crossings",       "crossings"),
    ("5-gons",          "kgons-5"),
    ("6-gons",          "kgons-6"),
    ("7-gons",          "kgons-7"),
    ("Empty 3-holes",   "empty-kgons-3"),
    ("Empty 4-holes",   "empty-kgons-4"),
    ("Empty 5-holes",   "empty-kgons-5"),
    ("Empty 6-holes",   "empty-kgons-6"),
    ("Empty 7-holes",   "empty-kgons-7"),
    ("Onion layers",    "onion-layers"),
    ("Triangulations",  "triangulations"),
]

DEFAULT_PROPERTIES: list[str] = [
    "hull", "crossings", "kgons-5", "kgons-6", "kgons-7",
    "empty-kgons-3", "empty-kgons-4", "empty-kgons-5", "empty-kgons-6",
]


def _compute_prop(sl, key: str):
    """Compute a single property from a SmallLambda."""
    if key == "hull":
        return len(sl.get_extremal_points())
    if key == "onion-layers":
        # count number of layers
        layers = 0
        remaining = list(range(sl.n))
        coords_orig = None  # not needed — use abstract
        # just count via iterative hull peeling on the SL
        from pyotlib2.core.small_lambda import SmallLambda
        current_sl = sl
        while current_sl.n >= 3:
            hull = current_sl.get_extremal_points()
            layers += 1
            remaining = [i for i in range(current_sl.n) if i not in hull]
            if len(remaining) < 3:
                if remaining:
                    layers += 1
                break
            # build sub-SL — not trivial abstractly; just return layer count approx
            break  # TODO: full onion peeling on abstract SL
        return layers
    if key == "crossings":
        from pyotlib2.algorithms.polygon_count import count_crossings
        return count_crossings(sl)
    if key.startswith("kgons-"):
        k = int(key.split("-")[1])
        from pyotlib2.algorithms.polygon_count import count_polygons
        bl = sl.to_big_lambda()
        return count_polygons(bl, k)
    if key.startswith("empty-kgons-"):
        k = int(key.split("-")[2])
        from pyotlib2.algorithms.mrsw import count_empty_kgons_mrsw
        return count_empty_kgons_mrsw(sl, k)
    if key == "triangulations":
        from pyotlib2.algorithms.triangulations import count_triangulations
        return count_triangulations(sl)
    raise ValueError(f"unknown property key: {key!r}")
