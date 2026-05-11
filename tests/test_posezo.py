"""Tests for PoSeZo singleton configurations.

Verifies known combinatorial properties of the PoSeZo database singletons:
https://www.eurogiga-compose.eu/posezo.php

Each test checks properties that are stated on the PoSeZo page and can be
computed by pyotlib2's current implementation (k-holes, hull, crossings).
"""

import pytest
from tests.point_configs import PoSeZo
from pyotlib2.algorithms.polygon_count import count_empty_kgons, count_crossings


# ---------------------------------------------------------------------------
# n10_c1_1_convex_5_hole: 10 pts, 1 convex 5-hole, hull=5
# ---------------------------------------------------------------------------

class TestN10OneConvex5Hole:
    def test_5_holes(self):
        """Exactly 1 convex 5-hole."""
        sl = PoSeZo.n10_c1_1_convex_5_hole()
        assert count_empty_kgons(sl, 5) == 1

    def test_hull_size(self):
        """Convex hull has 5 points."""
        sl = PoSeZo.n10_c1_1_convex_5_hole()
        bl = sl.to_big_lambda()
        assert len(bl.onion[0]) == 5

    def test_no_6_holes(self):
        """No convex 6-hole (only 10 points, would be too large)."""
        sl = PoSeZo.n10_c1_1_convex_5_hole()
        assert count_empty_kgons(sl, 6) == 0


# ---------------------------------------------------------------------------
# n12_c1_min_convex_3_4_5_holes: 12 pts, 3-holes=94, 4-holes=42, 5-holes=3
# ---------------------------------------------------------------------------

class TestN12MinHoles:
    def test_3_holes(self):
        """94 empty triangles."""
        sl = PoSeZo.n12_c1_min_convex_3_4_5_holes()
        assert count_empty_kgons(sl, 3) == 94

    def test_4_holes(self):
        """42 empty convex quadrilaterals."""
        sl = PoSeZo.n12_c1_min_convex_3_4_5_holes()
        assert count_empty_kgons(sl, 4) == 42

    def test_5_holes(self):
        """3 empty convex pentagons."""
        sl = PoSeZo.n12_c1_min_convex_3_4_5_holes()
        assert count_empty_kgons(sl, 5) == 3


# ---------------------------------------------------------------------------
# n12_c1_min_crossing_number_153: 12 pts, crossings=153
# ---------------------------------------------------------------------------

class TestN12MinCrossings:
    def test_crossing_number(self):
        """Rectilinear crossing number is 153."""
        sl = PoSeZo.n12_c1_min_crossing_number_153()
        assert count_crossings(sl) == 153


# ---------------------------------------------------------------------------
# n13_c1_min_convex_3_4_5_holes: 13 pts, 3-holes=114, 4-holes=51, 5-holes=3
# ---------------------------------------------------------------------------

class TestN13MinHoles:
    def test_3_holes(self):
        """114 empty triangles."""
        sl = PoSeZo.n13_c1_min_convex_3_4_5_holes()
        assert count_empty_kgons(sl, 3) == 114

    def test_4_holes(self):
        """51 empty convex quadrilaterals."""
        sl = PoSeZo.n13_c1_min_convex_3_4_5_holes()
        assert count_empty_kgons(sl, 4) == 51

    def test_5_holes(self):
        """3 empty convex pentagons."""
        sl = PoSeZo.n13_c1_min_convex_3_4_5_holes()
        assert count_empty_kgons(sl, 5) == 3


# ---------------------------------------------------------------------------
# n14_c1_6_convex_5_holes: 14 pts, 5-holes=6
# ---------------------------------------------------------------------------

class TestN14Six5Holes:
    def test_5_holes(self):
        """Exactly 6 convex 5-holes."""
        sl = PoSeZo.n14_c1_6_convex_5_holes()
        assert count_empty_kgons(sl, 5) == 6


# ---------------------------------------------------------------------------
# n15_c1_9_convex_5_holes: 15 pts, 5-holes=9
# ---------------------------------------------------------------------------

class TestN15Nine5Holes:
    def test_5_holes(self):
        """Exactly 9 convex 5-holes (minimum known for n=15)."""
        sl = PoSeZo.n15_c1_9_convex_5_holes()
        assert count_empty_kgons(sl, 5) == 9


# ---------------------------------------------------------------------------
# n29_c1_no_convex_6_hole: 29 pts, 5-holes=151, 6-holes=0
# ---------------------------------------------------------------------------

class TestN29No6Hole:
    def test_no_6_holes(self):
        """No convex 6-hole (largest known such set)."""
        sl = PoSeZo.n29_c1_no_convex_6_hole()
        assert count_empty_kgons(sl, 6) == 0

    def test_5_holes(self):
        """151 convex 5-holes."""
        sl = PoSeZo.n29_c1_no_convex_6_hole()
        assert count_empty_kgons(sl, 5) == 151
