"""Counting and enumeration of empty/convex k-gons in an order type.

All algorithms operate on BigLambda or SmallLambda objects — no concrete
coordinates required.

Glossary
--------
convex k-gon:  k points in convex position (no interior angles > 180°)
empty k-gon (k-hole):  convex k-gon with no other point of the set inside
"""

from __future__ import annotations
from itertools import combinations
from random import shuffle
from typing import Iterator

import numpy as np

import numpy as np

from pyotlib2.core.big_lambda import BigLambda
from pyotlib2.core.small_lambda import SmallLambda
from pyotlib2.core.utils import binomial


# ---------------------------------------------------------------------------
# Triangles
# ---------------------------------------------------------------------------

def _is_empty_triangle(o, a: int, b: int, c: int, potential_inner) -> bool:
    """Return True if triangle (a,b,c) contains no point from potential_inner.

    Uses numpy vectorized indexing: o[a,b,pts], o[b,c,pts], o[c,a,pts] are
    arrays — an interior point exists iff all three are == 1 simultaneously.
    By chirotope axioms, if o[a,b,c]==-1 we swap b↔c (o[a,c,b]==1).
    """
    if int(o[a, b, c]) != 1:
        # chirotope axiom: o[a,b,c]==-1 => o[a,c,b]==1, swap b and c
        return _is_empty_triangle(o, a, c, b, potential_inner)
    # numpy vectorization: computes all 3 orientation vectors at once via SIMD.
    # for large n this wins over lazy any(); for small n the difference is negligible.
    pts = potential_inner
    return not np.any((o[a, b, pts] == 1) & (o[b, c, pts] == 1) & (o[c, a, pts] == 1))


def enumerate_triangles(
    bl: BigLambda,
    empty_only: bool = True,
    shuffle_for_speedup: bool = True,
) -> Iterator[tuple]:
    """Yield triples (a, b, c) with a < b < c forming (empty) triangles.

    For each edge (a,b), splits c > b into left (o[a,b,c]==1) and right
    (o[a,b,c]==-1) sides and tests each side separately.
    Both sides yield valid triangles; the right side uses chirotope symmetry
    o[a,b,c]==-1  ↔  o[a,c,b]==1 (i.e. swap b↔c for the emptiness test).

    shuffle_for_speedup has no effect when _is_empty_triangle is vectorized
    (numpy checks all candidates simultaneously), but is kept for clarity and
    future Cython ports where sequential order matters again.
    """
    o = bl.o
    n = bl.n
    for a in range(n):
        for b in range(a + 1, n):
            cands = list(range(b + 1, n))
            left  = [c for c in cands if o[a, b, c] == 1]
            right = [c for c in cands if o[a, b, c] == -1]
            for side in (left, right):
                for c in side:
                    if empty_only and not _is_empty_triangle(o, a, b, c, side):
                        continue
                    yield (a, b, c)


def count_triangles(
    bl: BigLambda,
    empty_only: bool = True,
    maximum: int = None,
    shuffle_for_speedup: bool = True,
) -> int:
    cnt = 0
    for _ in enumerate_triangles(bl, empty_only, shuffle_for_speedup=shuffle_for_speedup):
        cnt += 1
        if maximum is not None and cnt > maximum:
            break
    return cnt


# ---------------------------------------------------------------------------
# Quadrilaterals — fast formula via SmallLambda
# ---------------------------------------------------------------------------

def count_crossings(sl: SmallLambda) -> int:
    """Count crossing pairs of edges (= convex quadrilaterals) via k-edges formula.

    This is an O(n²) abstract algorithm operating purely on the rank matrix l.
    See: countQuadrilaterals in old pyotlib/PolygonCount.py.
    """
    n = sl.n
    l = sl.get_l()
    kmax = (n - 3) // 2

    # e[k] = number of directed edge pairs (a,b) with min(l[a,b], l[b,a]) == k
    e = {k: 0 for k in range(kmax + 2)}
    for a, b in combinations(range(n), 2):
        e[min(int(l[a, b]), int(l[b, a]))] += 1

    # E[k] = cumulative sum of e[0..k]
    E = {k: sum(e[j] for j in range(k + 1)) for k in range(kmax + 1)}

    cn4 = E[(n - 3) // 2] if n % 2 == 1 else 0
    offset = (-3 * binomial(n, 3) + cn4)
    assert offset % 4 == 0
    offset //= 4

    return sum((n - 2 * k - 3) * E[k] for k in range(kmax + 1)) + offset


# ---------------------------------------------------------------------------
# General k-gon enumeration
# ---------------------------------------------------------------------------

def _assert_natural(o, n: int) -> None:
    """Assert that BigLambda has natural labeling: o[0,1,2] == o[0,i,i+1] for all i=1..n-2."""
    sign = int(o[0, 1, 2])
    consecutive = np.array([o[0, i, i+1] for i in range(1, n - 1)])
    assert np.all(consecutive == sign), \
        f"BigLambda is not naturally labeled: o[0,1,2]={sign} but got {consecutive}"


def _is_empty_polygon(o, selection: list, n: int, sign: int) -> bool:
    """Return True if the polygon given by selection contains no other point of the set."""
    k = len(selection)
    s = selection[0]
    for d in range(n):
        if d in selection:
            continue
        # d is inside iff o[selection[i], selection[i+1 % k], d] == sign for all i
        # but we only have the chain in selection order; the polygon is closed
        inside = all(int(o[selection[i], selection[(i + 1) % k], d]) == sign for i in range(k))
        if inside:
            return False
    return True


def enumerate_polygons(
    bl: BigLambda,
    k: int,
    empty_only: bool = True,
) -> Iterator[tuple]:
    """Yield k-tuples of point indices forming (empty) convex k-gons.

    Ported from old pyotlib enumeratePolygons / _enumeratePolygonsInner.
    Requires naturally-labeled BigLambda (asserted when empty_only=True).
    """
    n = bl.n
    o = bl.o
    sign = int(o[0, 1, 2])

    if empty_only:
        _assert_natural(o, n)

    def _is_empty_triangle(s: int, b: int, a: int, potential: list) -> bool:
        return not any(
            c not in (s, b, a)
            and int(o[s, b, c]) == int(o[s, b, a])
            and int(o[b, a, c]) == int(o[b, a, s])
            and int(o[a, s, c]) == int(o[a, s, b])
            for c in potential
        )

    def _inner(remaining_k: int, selection: list, potential: list) -> Iterator[tuple]:
        if len(potential) < remaining_k:
            return
        if remaining_k == 0:
            yield selection
            return
        b = selection[-1]
        s = selection[0]
        for a in potential:
            new_potential = [c for c in potential if c != a
                             and int(o[s, a, c]) == sign
                             and int(o[b, a, c]) == sign]
            if b != s and empty_only:
                if not _is_empty_triangle(s, b, a, potential):
                    continue
            yield from _inner(remaining_k - 1, selection + [a], new_potential)

    for pt in range(k - 1, n):
        pts = list(range(pt))
        shuffle(pts)
        yield from _inner(k - 1, [pt], pts)


def count_polygons(bl: BigLambda, k: int, empty_only: bool = True) -> int:
    return sum(1 for _ in enumerate_polygons(bl, k, empty_only))


# ---------------------------------------------------------------------------
# Convenience wrappers
# ---------------------------------------------------------------------------

def count_convex_kgons(sl: SmallLambda, k: int) -> int:
    return count_polygons(sl.to_big_lambda(), k, empty_only=False)


def count_empty_kgons(sl: SmallLambda, k: int) -> int:
    return count_polygons(sl.to_big_lambda(), k, empty_only=True)
