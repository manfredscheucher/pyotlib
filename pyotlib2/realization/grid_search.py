"""Randomized grid-search realization tester.

Ported from old/pyotlib/misc/simple_c/realize.c (Manfred Scheucher, 2013).

Algorithm
---------
Place n points one-by-one on a gridsize × gridsize integer grid.

For each new point the coordinates are found via *binary subdivision*:
starting from the full grid, at each bit level we pick a 2×2 sub-quadrant
(in random order) that is *not yet ruled out* for any existing pair (a,b).
A quadrant is ruled out for pair (a,b) if all four corners of the quadrant
yield the wrong orientation for o[a,b,new].

This gives an O(bits × n²) check per coordinate candidate (where bits =
log2(gridsize)), and the full backtracking search is randomised.

Forward-checking: after tentatively placing point k, we do a quick sanity
check that each remaining point k+1, …, n-1 can still be placed somewhere
in the grid (one random trial per remaining point).

The outer loop retries with fresh random seeds until success or max_tries
is exhausted.  Returns None (Undecided) when unsuccessful.
"""

from __future__ import annotations

import random
from typing import Optional

import numpy as np

from pyotlib2.core.small_lambda import SmallLambda
from pyotlib2.realization.base import RealizationTester, Undecided


# ---------------------------------------------------------------------------
# Orientation helper
# ---------------------------------------------------------------------------

def _orient(x: list, y: list, a: int, b: int, c: int) -> int:
    """Sign of the cross product (b-a)×(c-a): +1, -1, or 0."""
    v = (x[a] * (y[b] - y[c])
         + x[b] * (y[c] - y[a])
         + x[c] * (y[a] - y[b]))
    return (v > 0) - (v < 0)


# ---------------------------------------------------------------------------
# Core search
# ---------------------------------------------------------------------------

def _quad_allowed(
    qi: int, qj: int, qsize: int,
    old_count: int, new_idx: int,
    x: list, y: list,
    o: np.ndarray,
) -> bool:
    """Return True if the square [qi, qi+qsize) × [qj, qj+qsize) contains
    at least one position consistent with all orientation constraints for
    the pair (a, b) with a,b < old_count.

    A square is eliminated only when ALL FOUR corners give the wrong sign
    for some pair — adapted from quadAllowed() in realize.c.
    """
    if qsize == 1:
        # leaf: exact coordinate check
        x[new_idx] = qi
        y[new_idx] = qj
        for a in range(old_count):
            for b in range(a + 1, old_count):
                if _orient(x, y, a, b, new_idx) != o[a, b, new_idx]:
                    return False
        return True

    for a in range(old_count):
        for b in range(a + 1, old_count):
            wrong = 0
            for di in (0, qsize - 1):
                for dj in (0, qsize - 1):
                    x[new_idx] = qi + di
                    y[new_idx] = qj + dj
                    if _orient(x, y, a, b, new_idx) != o[a, b, new_idx]:
                        wrong += 1
            if wrong == 4:
                return False  # entire square on wrong side for this pair
    return True


def _find_valid_coords(
    bits: int,
    old_count: int,
    new_idx: int,
    x: list, y: list,
    o: np.ndarray,
    rng: random.Random,
) -> bool:
    """Binary subdivision search for a valid (x[new_idx], y[new_idx]).

    Returns True and sets x[new_idx], y[new_idx] on success.
    Corresponds to findValidCoords() in realize.c.
    """
    ci = cj = 0
    for bit in range(bits - 1, -1, -1):
        offset = 1 << bit
        prev_i, prev_j = ci, cj
        quadrants = [(0, 0), (0, 1), (1, 0), (1, 1)]
        rng.shuffle(quadrants)
        found = False
        for di, dj in quadrants:
            ni = prev_i + di * offset
            nj = prev_j + dj * offset
            if _quad_allowed(ni, nj, offset, old_count, new_idx, x, y, o):
                ci, cj = ni, nj
                found = True
                break
        if not found:
            return False
    # ci, cj is now the valid coordinate (offset==1 leaf was checked)
    x[new_idx] = ci
    y[new_idx] = cj
    return True


def _try_realize(
    n: int,
    gridsize: int,
    o: np.ndarray,
    max_trials: int,
    forward_check_trials: int,
    rng: random.Random,
) -> Optional[list]:
    """One backtracking attempt.  Returns list of (x, y) on success, else None.

    Corresponds to tryToFindRealisation() in realize.c.
    """
    bits = gridsize.bit_length() - 1  # gridsize must be a power of 2
    assert 1 << bits == gridsize, "gridsize must be a power of 2"

    x = [0] * n
    y = [0] * n

    def _recurse(point: int) -> bool:
        if point == n:
            return True

        tried = set()
        for _ in range(max_trials):
            if not _find_valid_coords(bits, point, point, x, y, o, rng):
                continue
            coord = (x[point], y[point])
            if coord in tried:
                continue
            tried.add(coord)

            # forward check: can each remaining point be placed?
            ok = True
            if forward_check_trials > 0:
                for other in range(point + 1, n):
                    placed = False
                    for _ in range(forward_check_trials):
                        if _find_valid_coords(bits, point + 1, other, x, y, o, rng):
                            placed = True
                            break
                    if not placed:
                        ok = False
                        break
            if not ok:
                continue

            if _recurse(point + 1):
                return True

        return False

    if _recurse(0):
        return list(zip(x, y))
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def grid_realize(
    sl: SmallLambda,
    gridsize: int = 256,
    max_trials: int = 100,
    forward_check_trials: int = 10,
    max_tries: int = 10,
    seed: Optional[int] = None,
) -> Optional[list]:
    """Try to find integer coordinates realizing the order type of sl.

    Parameters
    ----------
    sl : SmallLambda
        The abstract order type to realize.
    gridsize : int
        Side length of the integer grid (must be a power of 2).
        Default 256 (8-bit coords).
    max_trials : int
        Number of random coordinate attempts per point per recursion level.
    forward_check_trials : int
        Number of random attempts when forward-checking remaining points.
        Set to 0 to disable forward checking.
    max_tries : int
        Number of independent restarts (each with a fresh random seed).
    seed : int or None
        Random seed for reproducibility.

    Returns
    -------
    list of (x, y) tuples on success, None if no realization found.
    """
    # ensure gridsize is a power of 2
    bits = gridsize.bit_length() - 1
    gridsize = 1 << bits

    bl = sl.to_big_lambda()
    o = bl.o
    n = sl.n

    rng = random.Random(seed)
    for _ in range(max_tries):
        result = _try_realize(n, gridsize, o, max_trials, forward_check_trials, rng)
        if result is not None:
            return result
    return None


# ---------------------------------------------------------------------------
# RealizationTester integration
# ---------------------------------------------------------------------------

class GridSearchTester(RealizationTester):
    """Realization tester using randomized grid search.

    This is a Las Vegas algorithm: if it returns True the OT is definitely
    realizable (coordinates are found and verified).  If it returns False /
    raises Undecided, realizability is unknown — the search may have just
    failed to find coordinates within the given budget.

    Use a fallback tester (e.g. ScipyTester or GpTester) via the parent
    chain for a more definitive answer when this tester fails.
    """

    def __init__(
        self,
        gridsize: int = 256,
        max_trials: int = 100,
        forward_check_trials: int = 10,
        max_tries: int = 20,
        seed: Optional[int] = None,
        parent: Optional[RealizationTester] = None,
    ):
        super().__init__(parent)
        self.gridsize = gridsize
        self.max_trials = max_trials
        self.forward_check_trials = forward_check_trials
        self.max_tries = max_tries
        self.seed = seed

    def _test(self, ot: SmallLambda) -> bool:
        pts = grid_realize(
            ot,
            gridsize=self.gridsize,
            max_trials=self.max_trials,
            forward_check_trials=self.forward_check_trials,
            max_tries=self.max_tries,
            seed=self.seed,
        )
        if pts is not None:
            # attach realization to ot (mutate in place so caller sees it)
            ot.realization = pts
            return True
        raise Undecided("grid search exhausted without finding realization")
