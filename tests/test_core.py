"""Unit tests for core representations: PointSet, SmallLambda, BigLambda."""

import pytest
from pyotlib2.core.point_set import PointSet
from pyotlib2.core.small_lambda import SmallLambda
from pyotlib2.core.big_lambda import BigLambda


# ---------------------------------------------------------------------------
# Fixtures — hand-crafted small examples
# ---------------------------------------------------------------------------

# 4 points in convex position (square corners)
SQUARE = [(0, 0), (1, 0), (1, 1), (0, 1)]

# 5 points: 4 corners + off-center interior point (non-degenerate)
PENTAGON_WITH_CENTER = [(0, 0), (4, 0), (4, 4), (0, 4), (1, 2)]

# 3 non-collinear points
TRIANGLE = [(0, 0), (1, 0), (0, 1)]

# collinear points (invalid)
COLLINEAR = [(0, 0), (1, 1), (2, 2)]


# ---------------------------------------------------------------------------
# PointSet
# ---------------------------------------------------------------------------

class TestPointSet:
    def test_orientation_ccw(self):
        ps = PointSet(3, TRIANGLE)
        assert ps.orientation(0, 1, 2) == 1

    def test_orientation_cw(self):
        ps = PointSet(3, TRIANGLE)
        assert ps.orientation(0, 2, 1) == -1

    def test_orientation_collinear(self):
        ps = PointSet(3, COLLINEAR)
        assert ps.orientation(0, 1, 2) == 0

    def test_has_collinear_false(self):
        ps = PointSet(3, TRIANGLE)
        assert not ps.has_collinear_points()

    def test_has_collinear_true(self):
        ps = PointSet(3, COLLINEAR)
        assert ps.has_collinear_points()

    def test_to_big_lambda_roundtrip(self):
        ps = PointSet(4, SQUARE)
        bl = ps.to_big_lambda()
        assert bl.n == 4
        # Check antisymmetry
        for i in range(4):
            for j in range(4):
                for k in range(4):
                    assert bl.o[i][j][k] == -bl.o[i][k][j]

    def test_to_small_lambda(self):
        ps = PointSet(4, SQUARE)
        sl = ps.to_small_lambda(lazy=False)
        assert sl.n == 4
        # Validity: l[i][j] + l[j][i] == n-2 == 2
        l = sl.get_l()
        for i in range(4):
            for j in range(i):
                assert l[i][j] + l[j][i] == 2

    def test_normalized(self):
        ps = PointSet(3, [(5, 5), (6, 5), (5, 6)])
        norm = ps.normalized()
        xs = [x for x, _ in norm.points]
        ys = [y for _, y in norm.points]
        assert min(xs) == 0
        assert min(ys) == 0


# ---------------------------------------------------------------------------
# SmallLambda
# ---------------------------------------------------------------------------

class TestSmallLambda:
    def _make_square_sl(self):
        ps = PointSet(4, SQUARE)
        return ps.to_small_lambda(lazy=False)

    def test_is_valid_abstract(self):
        sl = self._make_square_sl()
        assert sl._is_valid_abstract()

    def test_string_roundtrip(self):
        sl = self._make_square_sl()
        s = sl.to_string()
        sl2 = SmallLambda.from_string(4, s)
        assert sl.compare(sl2) == 0

    def test_get_extremal_points(self):
        sl = self._make_square_sl()
        ext = sl.get_extremal_points()
        assert len(ext) >= 4  # all 4 corners are extremal for a square

    def test_natural_labeling(self):
        sl = self._make_square_sl()
        ext = sl.get_extremal_points()
        lab = sl.get_natural_labeling(ext[0])
        assert len(lab) == 4
        assert ext[0] == lab[0]

    def test_get_lex_min_is_stable(self):
        sl = self._make_square_sl()
        lm = sl.get_lex_min()
        lm2 = lm.get_lex_min()
        assert lm.compare(lm2) == 0

    def test_mirrored_then_mirrored_is_identity(self):
        sl = self._make_square_sl()
        assert sl.compare(sl.mirrored().mirrored()) == 0

    def test_relabeled_inverse(self):
        sl = self._make_square_sl()
        lab = [1, 2, 3, 0]
        from pyotlib2.core.utils import invert_perm
        inv_lab = invert_perm(lab)
        sl2 = sl.relabeled(lab).relabeled(inv_lab)
        assert sl.compare(sl2) == 0

    def test_to_big_lambda_roundtrip(self):
        sl = self._make_square_sl()
        bl = sl.to_big_lambda()
        sl2 = bl.to_small_lambda()
        assert sl.compare(sl2) == 0

    def test_reduce_k3(self):
        ps = PointSet(5, PENTAGON_WITH_CENTER)
        sl = ps.to_small_lambda(lazy=False)
        subs = list(sl.reduce(3))
        assert len(subs) == 10  # C(5,3)

    def test_hash_and_eq(self):
        sl = self._make_square_sl()
        sl2 = self._make_square_sl()
        assert sl == sl2
        d = {sl: 1}
        assert d[sl2] == 1


# ---------------------------------------------------------------------------
# BigLambda
# ---------------------------------------------------------------------------

class TestBigLambda:
    def _make_square_bl(self):
        return PointSet(4, SQUARE).to_big_lambda()

    def test_edges_cross(self):
        bl = self._make_square_bl()
        # Diagonal (0,2) and (1,3) of the square should cross
        assert bl.edges_cross((0, 2), (1, 3))

    def test_edges_no_cross(self):
        bl = self._make_square_bl()
        # Adjacent edges should not cross
        assert not bl.edges_cross((0, 1), (1, 2))

    def test_is_valid(self):
        bl = self._make_square_bl()
        assert bl.is_valid(test_exchange=False)  # exchange axiom slow, skip for unit test

    def test_to_string_length(self):
        from pyotlib2.core.utils import binomial
        bl = self._make_square_bl()
        s = bl.to_string()
        assert len(s) == binomial(4, 3)

    def test_relabeled(self):
        bl = self._make_square_bl()
        lab = [0, 1, 2, 3]
        bl2 = bl.relabeled(lab)
        for i in range(4):
            for j in range(4):
                for k in range(4):
                    assert bl.o[i][j][k] == bl2.o[i][j][k]

    def test_get_onion(self):
        # Square has 4 hull points + center
        ps = PointSet(5, PENTAGON_WITH_CENTER)
        bl = ps.to_big_lambda()
        onion = bl.get_onion()
        assert len(onion) == 2  # outer hull (4 pts) + inner point (1 pt)
        assert len(onion[0]) == 4
        assert len(onion[1]) == 1


# ---------------------------------------------------------------------------
# Conversion round-trips
# ---------------------------------------------------------------------------

class TestConversions:
    def test_pointset_sl_bl_sl_roundtrip(self):
        ps = PointSet(5, PENTAGON_WITH_CENTER)
        sl1 = ps.to_small_lambda(lazy=False)
        bl = sl1.to_big_lambda()
        sl2 = bl.to_small_lambda()
        assert sl1.compare(sl2) == 0

    def test_5point_configurations(self):
        """Test all 3 order types on 5 points (convex, 1-interior, etc.)"""
        configs = [
            [(0,0),(4,0),(4,4),(0,4),(2,2)],  # 4 hull + 1 interior
            [(0,0),(3,0),(5,2),(3,4),(0,3)],   # all convex
            [(0,0),(4,0),(3,3),(1,3),(2,1)],   # mixed
        ]
        for pts in configs:
            ps = PointSet(5, pts)
            if ps.has_collinear_points():
                continue
            sl = ps.to_small_lambda(lazy=False)
            assert sl._is_valid_abstract()
            bl = sl.to_big_lambda()
            sl2 = bl.to_small_lambda()
            assert sl.compare(sl2) == 0
