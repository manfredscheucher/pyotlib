"""PointSet: concrete 2D point coordinates with exact rational arithmetic.

Uses Python's built-in arbitrary-precision integers directly — no external
BigInteger library needed.  Fractions are used only where exact division is
required (e.g. the fast SmallLambda algorithm).
"""

from __future__ import annotations
from fractions import Fraction
from itertools import combinations
from typing import Optional

import numpy as np

from pyotlib2.core.utils import sign, ceil_log2


class PointSet:
    """A set of n points in the plane with exact integer or rational coordinates."""

    def __init__(
        self,
        n: int,
        points: list,
        coloring: Optional[dict] = None,
    ):
        assert len(points) == n
        self.n = n
        self.points = points
        self.coloring = coloring

    # ------------------------------------------------------------------
    # Orientation
    # ------------------------------------------------------------------

    def orientation(self, i: int, j: int, k: int) -> int:
        """Return sign of det([p_j-p_i, p_k-p_i]): +1 (CCW), -1 (CW), 0 (collinear)."""
        return sign(self._det(i, j, k))

    def _det(self, i: int, j: int, k: int) -> object:
        ix, iy = self.points[i]
        jx, jy = self.points[j]
        kx, ky = self.points[k]
        return ix * (jy - ky) + jx * (ky - iy) + kx * (iy - jy)

    # ------------------------------------------------------------------
    # Validity
    # ------------------------------------------------------------------

    def has_collinear_points(self) -> bool:
        for i, j, k in combinations(range(self.n), 3):
            if self.orientation(i, j, k) == 0:
                return True
        return False

    # ------------------------------------------------------------------
    # Conversions
    # ------------------------------------------------------------------

    def to_big_lambda(self) -> "BigLambda":
        from pyotlib2.core.big_lambda import BigLambda

        n = self.n
        o = np.zeros((n, n, n), dtype=np.int8)
        for i in range(n):
            for j in range(i + 1, n):
                for k in range(j + 1, n):
                    val = self.orientation(i, j, k)
                    o[i, j, k] = o[j, k, i] = o[k, i, j] = val
                    o[i, k, j] = o[j, i, k] = o[k, j, i] = -val
        return BigLambda(n, o, realization=self.points, coloring=self.coloring)

    def to_small_lambda(self, lazy: bool = True) -> "SmallLambda":
        from pyotlib2.core.small_lambda import SmallLambda

        if lazy:
            return SmallLambda(self.n, None, realization=self.points, coloring=self.coloring)
        if self.n < 30:
            return self._to_small_lambda_slow()
        return self._to_small_lambda_fast()

    def _to_small_lambda_slow(self) -> "SmallLambda":
        return self.to_big_lambda().to_small_lambda()

    def _to_small_lambda_fast(self) -> "SmallLambda":
        """O(n² log n) algorithm: sort by slope around each point."""
        from pyotlib2.core.small_lambda import SmallLambda

        n = self.n
        L = np.zeros((n, n), dtype=np.int32)
        X = [x for x, y in self.points]
        Y = [y for x, y in self.points]

        # Ensure all X-coordinates are distinct (apply shearing if needed)
        if len(set(X)) < n:
            if len(set(Y)) == n:
                X, Y = [-y for _, y in self.points], [x for x, _ in self.points]
            else:
                ymax = max(abs(y) for y in Y) or 1
                X = [x + Fraction(y, ymax * 10) for x, y in self.points]

        if len(set(X)) < n:
            return self._to_small_lambda_slow()

        for i0 in range(n):
            slopes = [
                Fraction(Y[i] - Y[i0], X[i] - X[i0]) if i != i0 else None
                for i in range(n)
            ]
            if len({s for s in slopes if s is not None}) < n - 1:
                return self._to_small_lambda_slow()

            R = sorted((i for i in range(n) if i != i0), key=lambda i: slopes[i])
            j0 = R[0]

            ct = sum(1 for k in range(n) if self.orientation(i0, j0, k) > 0)
            ct2 = sum(1 for k in range(n) if self.orientation(i0, j0, k) < 0)
            if ct + ct2 < n - 2:
                return self._to_small_lambda_slow()

            L[i0, j0] = ct
            sign_j0 = sign(X[j0] - X[i0])
            if sign_j0 == 0:
                return self._to_small_lambda_slow()

            for j in R[1:]:
                sign_j = sign(X[j] - X[i0]) * sign_j0
                if sign_j == 0:
                    return self._to_small_lambda_slow()
                ct -= sign_j
                L[i0, j] = ct if sign_j > 0 else n - 1 - ct

        return SmallLambda(n, L, realization=self.points, coloring=self.coloring)

    def get_lex_min(self) -> "PointSet":
        sl_min = self.to_small_lambda().get_lex_min()
        assert sl_min.realization is not None
        return PointSet(sl_min.n, sl_min.realization, coloring=self.coloring)

    # ------------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------------

    def normalized(self) -> "PointSet":
        xmin = min(x for x, _ in self.points)
        ymin = min(y for _, y in self.points)
        return PointSet(
            self.n, [(x - xmin, y - ymin) for x, y in self.points], coloring=self.coloring
        )

    def diameter(self) -> object:
        norm = self.normalized()
        xs = [x for x, _ in norm.points]
        ys = [y for _, y in norm.points]
        return max(max(xs) - min(xs), max(ys) - min(ys))

    def bits(self) -> int:
        return ceil_log2(1 + self.diameter())
