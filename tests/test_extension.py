"""Tests for extend_abstract: iterative extension from n=3 counts must match known values.

Known counts of abstract order types (= realizable for n<=8):
  n=3:   1
  n=4:   2
  n=5:   3
  n=6:  16
  n=7: 135
  n=8: 3315  (slow)

OEIS A006247 (abstract), A063666 (realizable) — all equal for n<=8.
"""

import numpy as np
import pytest
from pyotlib2.core.big_lambda import BigLambda
from pyotlib2.cli.commands import extend_abstract


def _single_n3_ot():
    """The unique order type on 3 points (all in convex position)."""
    o = np.zeros((3, 3, 3), dtype=np.int8)
    o[0, 1, 2] = o[1, 2, 0] = o[2, 0, 1] = 1
    o[0, 2, 1] = o[2, 1, 0] = o[1, 0, 2] = -1
    return BigLambda(3, o).to_small_lambda()


def _extend_all(ots, method="recursive"):
    """Extend each OT in ots by one point, deduplicate, return list."""
    seen = {}
    for ot in ots:
        for ext in extend_abstract(ot, method=method):
            key = ext.to_string()
            seen[key] = ext
    return list(seen.values())


@pytest.fixture(scope="module")
def ots_n3():
    return [_single_n3_ot()]


@pytest.fixture(scope="module")
def ots_n4(ots_n3):
    return _extend_all(ots_n3)


@pytest.fixture(scope="module")
def ots_n5(ots_n4):
    return _extend_all(ots_n4)


@pytest.fixture(scope="module")
def ots_n6(ots_n5):
    return _extend_all(ots_n5)


@pytest.fixture(scope="module")
def ots_n7(ots_n6):
    return _extend_all(ots_n6)


class TestExtensionCounts:
    def test_n3(self, ots_n3):
        assert len(ots_n3) == 1

    def test_n4(self, ots_n4):
        assert len(ots_n4) == 2

    def test_n5(self, ots_n5):
        assert len(ots_n5) == 3

    def test_n6(self, ots_n6):
        assert len(ots_n6) == 16

    def test_n7(self, ots_n7):
        assert len(ots_n7) == 135

    @pytest.mark.slow
    def test_n8(self, ots_n7):
        ots_n8 = _extend_all(ots_n7)
        assert len(ots_n8) == 3315


class TestExtensionSatCounts:
    """SAT method must give the same counts."""

    def test_n4_sat(self, ots_n3):
        assert len(_extend_all(ots_n3, method="sat")) == 2

    def test_n5_sat(self, ots_n3):
        n4 = _extend_all(ots_n3, method="sat")
        assert len(_extend_all(n4, method="sat")) == 3

    def test_n6_sat(self, ots_n3):
        n4 = _extend_all(ots_n3, method="sat")
        n5 = _extend_all(n4, method="sat")
        assert len(_extend_all(n5, method="sat")) == 16


class TestExtensionValidity:
    """Each extended OT must be a valid chirotope."""

    def test_n4_valid(self, ots_n4):
        for ot in ots_n4:
            assert ot.to_big_lambda().is_valid(print_collinear_warning=False)

    def test_n5_valid(self, ots_n5):
        for ot in ots_n5:
            assert ot.to_big_lambda().is_valid(print_collinear_warning=False)

    def test_n6_valid(self, ots_n6):
        for ot in ots_n6:
            assert ot.to_big_lambda().is_valid(print_collinear_warning=False)
