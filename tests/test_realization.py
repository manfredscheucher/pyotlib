"""Tests for realization methods.

Covers: grid_realize, GridSearchTester.
"""

import pytest
from pyotlib2.core.point_set import PointSet
from pyotlib2.realization.grid_search import grid_realize, GridSearchTester
from tests.point_configs import (
    convex_position_moment_curve as _convex,
    one_interior,
    abstract_only,
)


def _abstract(n):
    return abstract_only(_convex(n))


# ---------------------------------------------------------------------------
# grid_realize
# ---------------------------------------------------------------------------

class TestGridRealize:
    def test_convex5_found(self):
        """Convex 5-gon is realizable and grid search finds coordinates."""
        sl = _abstract(5)
        pts = grid_realize(sl, gridsize=32, max_trials=50, max_tries=5, seed=0)
        assert pts is not None
        assert len(pts) == 5

    def test_coordinates_correct(self):
        """Found coordinates realize the correct order type."""
        sl = _abstract(6)
        pts = grid_realize(sl, gridsize=64, max_trials=100, max_tries=10, seed=1)
        assert pts is not None
        ps = PointSet(6, pts)
        sl2 = ps.to_small_lambda(lazy=False)
        assert sl2.to_string() == sl.to_string()

    def test_n8_realizable(self):
        """n=8 abstract OT (convex) is realized within grid."""
        sl = _abstract(8)
        pts = grid_realize(sl, gridsize=64, max_trials=100, max_tries=10, seed=42)
        assert pts is not None
        ps = PointSet(8, pts)
        sl2 = ps.to_small_lambda(lazy=False)
        assert sl2.to_string() == sl.to_string()

    def test_with_interior_point(self):
        """OT with 1 interior point is realized correctly."""
        sl = abstract_only(one_interior(6))
        pts = grid_realize(sl, gridsize=64, max_trials=100, max_tries=10, seed=7)
        assert pts is not None
        ps = PointSet(sl.n, pts)
        sl2 = ps.to_small_lambda(lazy=False)
        assert sl2.to_string() == sl.to_string()

    def test_coords_in_grid(self):
        """All coordinates lie within [0, gridsize-1]."""
        gridsize = 32
        sl = _abstract(5)
        pts = grid_realize(sl, gridsize=gridsize, max_trials=50, max_tries=5, seed=0)
        assert pts is not None
        for x, y in pts:
            assert 0 <= x < gridsize
            assert 0 <= y < gridsize

    def test_gridsize_not_power_of_two_rounded(self):
        """Non-power-of-2 gridsize is silently rounded down to nearest power of 2."""
        sl = _abstract(4)
        pts = grid_realize(sl, gridsize=100, max_trials=50, max_tries=5, seed=0)
        assert pts is not None


# ---------------------------------------------------------------------------
# GridSearchTester
# ---------------------------------------------------------------------------

class TestGridSearchTester:
    def test_realizable_returns_true(self):
        """Realizable OT returns True."""
        sl = _abstract(5)
        tester = GridSearchTester(gridsize=32, max_tries=10, seed=0)
        assert tester.is_realizable(sl) is True

    def test_attaches_realization(self):
        """After success, ot.realization is set."""
        sl = _abstract(5)
        tester = GridSearchTester(gridsize=32, max_tries=10, seed=0)
        tester.is_realizable(sl)
        assert sl.realization is not None
        assert len(sl.realization) == sl.n

    def test_realization_correct(self):
        """Attached realization realizes the correct order type."""
        sl = _abstract(6)
        tester = GridSearchTester(gridsize=64, max_tries=10, seed=2)
        tester.is_realizable(sl)
        assert sl.realization is not None
        ps = PointSet(sl.n, sl.realization)
        sl2 = ps.to_small_lambda(lazy=False)
        assert sl2.to_string() == sl.to_string()

    def test_undecided_on_zero_tries(self):
        """With max_tries=0 the tester immediately raises Undecided."""
        from pyotlib2.realization.base import Undecided
        sl = _abstract(5)
        tester = GridSearchTester(gridsize=32, max_tries=0, seed=0)
        with pytest.raises(Undecided):
            tester._test(sl)
