"""Algorithm tests using the Graz order type database."""

import pytest
from pyotlib2.io.readers import read_order_types
from pyotlib2.algorithms.unify import unify


class TestReadAndValidate:
    def test_read_n6(self, otypes_path):
        """DB for n=6 is readable and non-empty."""
        path = otypes_path(6)
        ots = list(read_order_types(path, n=6))
        assert len(ots) > 0

    def test_all_n5_valid(self, otypes_path):
        """All raw OTs for n=5 pass the abstract validity check."""
        path = otypes_path(5)
        for ot in read_order_types(path, n=5):
            assert ot._is_valid_abstract()


class TestUnify:
    @pytest.mark.parametrize("n,expected", [
        (3, 1), (4, 2), (5, 3), (6, 16), (7, 135), (8, 3315)
    ])
    def test_unify_lex_min_count(self, otypes_path, n, expected):
        """After lex-min unification, exactly the known number of OTs remain.

        The Graz database already contains one representative per
        lex-min equivalence class, so unify() should yield the same count
        as the DB (no further merging) AND every OT should already be its
        own lex-min representative.
        """
        path = otypes_path(n)
        unique = list(unify(read_order_types(path, n=n)))
        assert len(unique) == expected, f"n={n}: expected {expected}, got {len(unique)}"
        for ot in unique:
            assert ot == ot.get_lex_min(), f"n={n}: DB entry is not lex-min: {ot.to_string()}"


class TestEmptyTriangles:
    def test_harborth_lower_bound_n6(self, otypes_path):
        """All n=6 OTs have at least 4 empty triangles (Harborth lower bound for n≥5)."""
        from pyotlib2.algorithms.polygon_count import count_triangles
        path = otypes_path(6)
        for ot in unify(read_order_types(path, n=6)):
            bl = ot.to_big_lambda()
            cnt = count_triangles(bl, empty_only=True)
            assert cnt >= 4, f"Only {cnt} empty triangles"


class TestProjectiveClasses:
    """Projective equivalence classes of order types.

    Projective classes correspond exactly to isomorphism classes of
    non-degenerate rank-3 oriented matroids (abstract order types in the
    projective sense).  Two order types are in the same class iff one can
    be obtained from the other by a sequence of extremal-point reflections
    (flips on the flip graph).

    Catalogue: https://finschi.com/math/om/?p=catom&filter=nondeg
    Expected counts (all realizable):
      n=5 →     1
      n=6 →     4
      n=7 →    11
      n=8 →   135
      n=9 →  4381  (4380 realizable + 1 non-realizable)
    """

    @pytest.mark.parametrize("n,expected", [
        (5, 1), (6, 4), (7, 11), (8, 135)
    ])
    def test_projective_class_count(self, otypes_path, n, expected):
        from pyotlib2.algorithms.projective_class import ProjectiveClass
        path = otypes_path(n)
        ots = list(unify(read_order_types(path, n=n)))
        representers = set()
        for ot in ots:
            pc = ProjectiveClass(ot)
            representers.add(pc.representer.to_string())
        assert len(representers) == expected, (
            f"n={n}: expected {expected} projective classes, got {len(representers)}"
        )

    @pytest.mark.slow
    def test_projective_class_count_n9(self, otypes_path):
        """n=9 has 4381 projective classes (4380 realizable + 1 non-realizable).

        Marked slow — takes several minutes.  Run with: pytest -m slow
        """
        from pyotlib2.algorithms.projective_class import ProjectiveClass
        path = otypes_path(9)
        ots = list(unify(read_order_types(path, n=9)))
        representers = set()
        for ot in ots:
            pc = ProjectiveClass(ot)
            representers.add(pc.representer.to_string())
        assert len(representers) == 4381, (
            f"n=9: expected 4381 projective classes, got {len(representers)}"
        )
