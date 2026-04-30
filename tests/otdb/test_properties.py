"""Tests that verify computed properties for every OT in the Graz order type database.

For each order type we check:
  - extremal points: 3 <= extrem <= n
  - convex n-gon:    exactly 1 if all points convex, else 0
  - empty triangles: at least 1 (every point set has an empty triangle)
  - empty 4-gons:    Harborth: every set of >= 5 points has an empty convex 4-gon
  - crossing number: equals count_polygons(k=4, empty=False)
                     i.e. count_crossings == number of convex 4-gons
"""

import pytest
from pyotlib2.io.readers import read_order_types
from pyotlib2.algorithms.polygon_count import (
    count_crossings,
    count_polygons,
    count_triangles,
)


@pytest.mark.requires_data
class TestExtremalPoints:
    @pytest.mark.parametrize("n", [3, 4, 5, 6, 7, 8])
    def test_extremal_range(self, otypes_path, n):
        """Every OT has between 3 and n extremal (hull) points."""
        path = otypes_path(n)
        for ot in read_order_types(path, n=n):
            ext = len(ot.extremal_points)
            assert 3 <= ext <= n, (
                f"n={n}: extremal={ext} out of range [3,{n}] for {ot.to_string()[:40]}"
            )


@pytest.mark.requires_data
class TestConvexNGon:
    @pytest.mark.parametrize("n", [3, 4, 5, 6, 7, 8])
    def test_convex_ngon_count(self, otypes_path, n):
        """An OT has exactly 1 convex n-gon iff all n points are in convex position
        (i.e. all n points are extremal), else 0."""
        path = otypes_path(n)
        for ot in read_order_types(path, n=n):
            bl = ot.big_lambda
            cnt = count_polygons(bl, n, empty_only=False)
            all_convex = len(ot.extremal_points) == n
            expected = 1 if all_convex else 0
            assert cnt == expected, (
                f"n={n}: convex {n}-gon count={cnt}, expected={expected}, "
                f"extremal={len(ot.extremal_points)}"
            )


@pytest.mark.requires_data
class TestEmptyTriangles:
    @pytest.mark.parametrize("n", [3, 4, 5, 6, 7, 8])
    def test_at_least_one_empty_triangle(self, otypes_path, n):
        """Every point set in general position has at least one empty triangle."""
        path = otypes_path(n)
        for ot in read_order_types(path, n=n):
            bl = ot.big_lambda
            cnt = count_triangles(bl, empty_only=True)
            assert cnt >= 1, f"n={n}: no empty triangle found"

    @pytest.mark.parametrize("n", [5, 6, 7, 8])
    def test_harborth_lower_bound(self, otypes_path, n):
        """Harborth (1978): every set of >= 5 points has at least 4 empty triangles."""
        path = otypes_path(n)
        for ot in read_order_types(path, n=n):
            bl = ot.big_lambda
            cnt = count_triangles(bl, empty_only=True)
            assert cnt >= 4, f"n={n}: only {cnt} empty triangles (Harborth requires >= 4)"


@pytest.mark.requires_data
class TestEmptyKGons:
    @pytest.mark.parametrize("n", [5, 6, 7, 8])
    def test_harborth_empty_4gon(self, otypes_path, n):
        """Harborth (1978): every set of >= 5 points has at least one empty convex 4-gon."""
        path = otypes_path(n)
        for ot in read_order_types(path, n=n):
            bl = ot.big_lambda
            cnt = count_polygons(bl, 4, empty_only=True)
            assert cnt >= 1, f"n={n}: no empty convex 4-gon found"

    @pytest.mark.parametrize("n", [3, 4, 5, 6, 7, 8])
    def test_empty_ngon_at_most_one(self, otypes_path, n):
        """At most 1 empty n-gon (only convex position has one)."""
        path = otypes_path(n)
        for ot in read_order_types(path, n=n):
            bl = ot.big_lambda
            cnt = count_polygons(bl, n, empty_only=True)
            assert cnt <= 1, f"n={n}: {cnt} empty {n}-gons (expected 0 or 1)"


@pytest.mark.requires_data
class TestCrossingNumber:
    @pytest.mark.parametrize("n", [3, 4, 5, 6, 7, 8])
    def test_crossing_number_equals_convex_4gons(self, otypes_path, n):
        """count_crossings(sl) == count_polygons(bl, k=4, empty=False).

        The rectilinear crossing number equals the number of convex 4-gons
        (each crossing pair of edges corresponds to exactly one convex quadrilateral).
        """
        path = otypes_path(n)
        for ot in read_order_types(path, n=n):
            bl = ot.big_lambda
            by_formula = count_crossings(ot)
            by_enum = count_polygons(bl, 4, empty_only=False)
            assert by_formula == by_enum, (
                f"n={n}: count_crossings={by_formula} != count_4gons={by_enum}"
            )
