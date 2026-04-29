"""Realizability via nonlinear optimization (scipy).

Attempts to find a concrete point set realizing the given order type by
minimizing a quality function that penalizes orientation violations.
"""

from __future__ import annotations
import random
from fractions import Fraction
from typing import Optional

from pyotlib2.core.small_lambda import SmallLambda
from pyotlib2.core.point_set import PointSet
from pyotlib2.core.utils import lcm
from pyotlib2.realization.base import RealizationTester, Undecided

try:
    import scipy.optimize as _scipy_opt
    _HAS_SCIPY = True
except ImportError:
    _HAS_SCIPY = False


class ScipyRealizationTester(RealizationTester):
    """Nonlinear optimization-based realization tester.

    Minimises sum of squared orientation violations over random starting points.
    """

    def __init__(
        self,
        parent: Optional[RealizationTester] = None,
        trials: int = 20,
        methods: tuple = ("Nelder-Mead", "Powell", "L-BFGS-B"),
        coord_range: int = 100,
    ):
        super().__init__(parent)
        if not _HAS_SCIPY:
            raise RuntimeError("scipy is required for ScipyRealizationTester")
        self.trials = trials
        self.methods = methods
        self.coord_range = coord_range

    def _test(self, ot: SmallLambda) -> bool:
        bl = ot.to_big_lambda()
        n = bl.n
        o_arr = bl.o

        def quality(flat_coords):
            pts = [(flat_coords[2 * i], flat_coords[2 * i + 1]) for i in range(n)]
            total = 0.0
            for i in range(n):
                for j in range(i + 1, n):
                    for k in range(j + 1, n):
                        ix, iy = pts[i]
                        jx, jy = pts[j]
                        kx, ky = pts[k]
                        det = ix * (jy - ky) + jx * (ky - iy) + kx * (iy - jy)
                        expected = o_arr[i][j][k]
                        if expected * det <= 0:
                            total += (det - expected) ** 2
            return total

        for _ in range(self.trials):
            x0 = [random.uniform(-self.coord_range, self.coord_range) for _ in range(2 * n)]
            for method in self.methods:
                try:
                    res = _scipy_opt.minimize(quality, x0, method=method, options={"maxiter": 10000})
                    if res.fun < 1e-6:
                        # Try to convert to integer coordinates
                        pts = self._to_integer(res.x, n)
                        if pts is not None:
                            ps = PointSet(n, pts)
                            sl = ps.to_small_lambda(lazy=False)
                            if sl.compare(ot.get_lex_min()) == 0:
                                return True
                except Exception:
                    pass

        raise Undecided("scipy optimization did not find a realization")

    def _to_integer(self, flat, n, scale=1000):
        """Try to snap float coordinates to integers."""
        try:
            pts = []
            for i in range(n):
                x = round(flat[2 * i] * scale)
                y = round(flat[2 * i + 1] * scale)
                pts.append((x, y))
            return pts
        except Exception:
            return None
