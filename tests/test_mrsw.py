"""Tests for the MRSW k-hole counting algorithm.

Verifies count_empty_kgons_mrsw against the reference implementation
(count_empty_kgons) on a variety of configurations.
"""

import pytest
from tests.point_configs import (
    convex_position_moment_curve as _convex,
    one_interior,
    abstract_only,
    PoSeZo,
)
from pyotlib2.algorithms.mrsw import count_empty_kgons_mrsw, count_all_kgons_mrsw
from pyotlib2.algorithms.polygon_count import count_empty_kgons


# ---------------------------------------------------------------------------
# Convex position
# ---------------------------------------------------------------------------

class TestMrswConvex:
    @pytest.mark.parametrize("n,k,expected", [
        (4, 3, 4), (4, 4, 1),
        (5, 3, 10), (5, 4, 5), (5, 5, 1),
        (6, 3, 20), (6, 4, 15), (6, 5, 6), (6, 6, 1),
        (7, 3, 35), (7, 4, 35), (7, 5, 21), (7, 6, 7), (7, 7, 1),
    ])
    def test_convex_kgons(self, n, k, expected):
        sl = abstract_only(_convex(n))
        assert count_empty_kgons_mrsw(sl, k) == expected

    def test_matches_reference_n8(self):
        """MRSW matches reference for all k on convex 8-gon."""
        sl = abstract_only(_convex(8))
        for k in range(3, 9):
            assert count_empty_kgons_mrsw(sl, k) == count_empty_kgons(sl, k)


# ---------------------------------------------------------------------------
# Interior points
# ---------------------------------------------------------------------------

class TestMrswInterior:
    def test_one_interior_n6_all_k(self):
        """MRSW matches reference for all k on n=6 with 1 interior point."""
        sl = abstract_only(one_interior(6))
        for k in range(3, 7):
            assert count_empty_kgons_mrsw(sl, k) == count_empty_kgons(sl, k)

    def test_one_interior_n7_all_k(self):
        """MRSW matches reference for all k on n=7 with 1 interior point."""
        sl = abstract_only(one_interior(7))
        for k in range(3, 8):
            assert count_empty_kgons_mrsw(sl, k) == count_empty_kgons(sl, k)


# ---------------------------------------------------------------------------
# count_all_kgons_mrsw
# ---------------------------------------------------------------------------

class TestMrswCountAll:
    def test_count_all_convex5(self):
        sl = abstract_only(_convex(5))
        counts = count_all_kgons_mrsw(sl, k_max=5)
        assert counts == {3: 10, 4: 5, 5: 1}

    def test_count_all_matches_reference(self):
        sl = abstract_only(_convex(6))
        counts = count_all_kgons_mrsw(sl, k_max=6)
        for k in range(3, 7):
            assert counts[k] == count_empty_kgons(sl, k)

    def test_count_all_interior(self):
        sl = abstract_only(one_interior(6))
        counts = count_all_kgons_mrsw(sl, k_max=5)
        for k in range(3, 6):
            assert counts[k] == count_empty_kgons(sl, k)


# ---------------------------------------------------------------------------
# PoSeZo known values
# ---------------------------------------------------------------------------

class TestMrswPoSeZo:
    def test_n10_5holes(self):
        sl = PoSeZo.n10_c1_1_convex_5_hole()
        assert count_empty_kgons_mrsw(sl, 5) == 1

    def test_n12_3holes(self):
        sl = PoSeZo.n12_c1_min_convex_3_4_5_holes()
        assert count_empty_kgons_mrsw(sl, 3) == 94

    def test_n12_4holes(self):
        sl = PoSeZo.n12_c1_min_convex_3_4_5_holes()
        assert count_empty_kgons_mrsw(sl, 4) == 42

    def test_n12_5holes(self):
        sl = PoSeZo.n12_c1_min_convex_3_4_5_holes()
        assert count_empty_kgons_mrsw(sl, 5) == 3

    def test_n29_no_6holes(self):
        """MRSW confirms no convex 6-hole in the n=29 Horton-type set."""
        sl = PoSeZo.n29_c1_no_convex_6_hole()
        assert count_empty_kgons_mrsw(sl, 6) == 0

    def test_n29_5holes(self):
        sl = PoSeZo.n29_c1_no_convex_6_hole()
        assert count_empty_kgons_mrsw(sl, 5) == 151


# ---------------------------------------------------------------------------
# OTDB cross-check (n=3..6)
# ---------------------------------------------------------------------------

def _otdb_path(n: int):
    from pathlib import Path
    root = Path(__file__).parent / "otdb" / "otypes"
    ext = "b08" if n <= 8 else "b16"
    p = root / f"otypes{n:02d}.{ext}"
    return p if p.exists() else None


class TestMrswOtdb:
    @pytest.mark.parametrize("n", [3, 4, 5, 6])
    def test_matches_reference_all_ots(self, n):
        """MRSW matches reference implementation for all OTs in otypes0n."""
        from pyotlib2.io.readers import read_order_types
        path = _otdb_path(n)
        if path is None:
            pytest.skip(f"otypes{n:02d} not found — run tests/otdb/download.py first")
        for sl in read_order_types(path, n=n):
            for k in range(3, n + 1):
                assert count_empty_kgons_mrsw(sl, k) == count_empty_kgons(sl, k), \
                    f"n={n} k={k} OT={sl.to_string().strip()}"
