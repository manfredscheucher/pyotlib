"""CLI command implementations for pyotlib2.

Each command is also importable as a regular Python function for use in
IPython / Jupyter notebooks.

Two conceptually different optimization modes
---------------------------------------------

**Coordinate minimization** — preserves the order type
    The abstract order type (all triple orientations) stays fixed.
    Only the concrete integer coordinates are changed.
    All combinatorial properties (crossings, k-gons, …) are invariant.

    Commands:  minimize-coords   beautify-coords (--method gd|nm)

**Property minimization / local search** — changes the order type
    The OT itself is modified (triple orientations may flip).
    The goal is to find a *different* OT with a better property value.

    walk-points   -- needs concrete coordinates; moves points in coordinate
                     space (DFS) or randomly (--random).
    walk-abstract -- purely abstract; flips exit-edge triples on the
                     chirotope (DFS or --random).

    Commands:  walk-points   walk-abstract
"""

from __future__ import annotations
import argparse
import sys
from typing import Iterable, Iterator, Optional

from pyotlib2.core.small_lambda import SmallLambda
from pyotlib2.io.readers import read_order_types
from pyotlib2.io.writers import write_order_types
from pyotlib2.cli.io_args import (
    add_input_args, add_output_args, open_input, resolve_output, progress_iter
)


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def register_all(sub) -> None:
    # OT-level
    _register_unify(sub)
    _register_lexmin(sub)
    _register_sort(sub)
    _register_shuffle(sub)
    _register_enum_subconf(sub)
    _register_count_subconf(sub)
    _register_find_subconf(sub)
    # PC-level
    _register_enum_projective(sub)
    _register_enum_natural(sub)
    # Properties
    _register_kgons(sub)
    _register_properties(sub)
    # Realization
    _register_realize(sub)
    _register_smart_realize(sub)
    _register_gp_test(sub)
    _register_minimize_coords(sub)
    _register_beautify_coords(sub)
    # Local search / property optimization
    _register_walk_points(sub)
    _register_walk_abstract(sub)
    # Extension
    _register_extend_abstract(sub)
    _register_extend_random(sub)
    # Visualization
    _register_plot(sub)
    _register_editor(sub)


# ---------------------------------------------------------------------------
# unify
# ---------------------------------------------------------------------------

def unify_ot(
    ots: Iterable[SmallLambda],
    calc_lex_min: bool = True,
    validate: bool = True,
) -> Iterator[SmallLambda]:
    """Remove duplicate order types via lex-min deduplication."""
    from pyotlib2.algorithms.unify import unify as _unify
    yield from _unify(ots, calc_lex_min=calc_lex_min, validate=validate)


def _register_unify(sub) -> None:
    p = sub.add_parser(
        "unify",
        help="Remove duplicate order types (or projective classes with --projective)",
        description=(
            "Deduplicate order types by computing the lex-min representative "
            "of each and removing duplicates.  The output contains exactly one "
            "representative per distinct (abstract) order type.  "
            "With --projective, deduplicates at the level of projective classes "
            "(rank-3 oriented matroid isomorphism classes)."
        ),
    )
    add_input_args(p)
    add_output_args(p, ".uniq")
    p.add_argument("--no-lexmin", action="store_false", dest="calc_lex_min",
                   help="Skip lex-min normalization")
    p.add_argument("--no-validate", action="store_false", dest="validate",
                   help="Skip collinearity check")
    p.add_argument("--projective", action="store_true",
                   help="Deduplicate projective classes instead of order types")
    p.set_defaults(func=_cmd_unify, calc_lex_min=True, validate=True, projective=False)


def _cmd_unify(args) -> None:
    if args.projective:
        ots_in = list(open_input(args))
        total = len(ots_in)
        unique = list(unify_pc(iter(ots_in)))
        out, fmt = resolve_output(args, ".uniq.lt")
        write_order_types(unique, out, fmt=fmt)
        print(f"total: {total}  unique PCs: {len(unique)}  written to: {out}")
    else:
        ots = list(open_input(args))
        total = len(ots)
        unique = list(unify_ot(iter(ots), calc_lex_min=args.calc_lex_min, validate=args.validate))
        out, fmt = resolve_output(args, ".uniq.lt")
        write_order_types(unique, out, fmt=fmt)
        print(f"total: {total}  unique: {len(unique)}  written to: {out}")


# ---------------------------------------------------------------------------
# lexmin
# ---------------------------------------------------------------------------

def lex_min_ot(ots: Iterable[SmallLambda]) -> Iterator[SmallLambda]:
    """Relabel each order type to its lex-min representative."""
    for ot in ots:
        yield ot.get_lex_min()


def _register_lexmin(sub) -> None:
    p = sub.add_parser(
        "lexmin",
        help="Relabel order types to lex-min representative (or PC representer with --projective)",
        description=(
            "Relabel each order type to its lexicographically minimal "
            "representative (canonical form under point relabeling).  "
            "With --projective, relabels to the PC representer of its "
            "projective class (rank-3 oriented matroid isomorphism class)."
        ),
    )
    add_input_args(p)
    add_output_args(p, ".lexmin")
    p.add_argument("--projective", action="store_true",
                   help="Relabel to PC representer instead of OT lex-min")
    p.set_defaults(func=_cmd_lexmin, projective=False)


def _cmd_lexmin(args) -> None:
    if args.projective:
        ots = list(lex_min_pc(open_input(args)))
        out, fmt = resolve_output(args, ".lexmin.lt")
        write_order_types(ots, out, fmt=fmt)
        print(f"written: {len(ots)}  to: {out}")
    else:
        ots = list(lex_min_ot(open_input(args)))
        out, fmt = resolve_output(args, ".lexmin.lt")
        write_order_types(ots, out, fmt=fmt)
        print(f"written: {len(ots)}  to: {out}")


# ---------------------------------------------------------------------------
# sort
# ---------------------------------------------------------------------------

def sort(ots: Iterable[SmallLambda]) -> list:
    """Return order types sorted lexicographically."""
    return sorted(ots)


def _register_sort(sub) -> None:
    p = sub.add_parser(
        "sort",
        help="Sort order types lexicographically",
        description="Sort order types into lexicographic order.",
    )
    add_input_args(p)
    add_output_args(p, ".sorted")
    p.set_defaults(func=_cmd_sort)


def _cmd_sort(args) -> None:
    ots = sort(open_input(args))
    out, fmt = resolve_output(args, ".sorted.lt")
    write_order_types(ots, out, fmt=fmt)
    print(f"written: {len(ots)}  to: {out}")


# ---------------------------------------------------------------------------
# shuffle
# ---------------------------------------------------------------------------

def shuffle(ots: Iterable[SmallLambda]) -> list:
    """Return order types in random order."""
    import random
    lst = list(ots)
    random.shuffle(lst)
    return lst


def _register_shuffle(sub) -> None:
    p = sub.add_parser(
        "shuffle",
        help="Shuffle order types randomly",
        description="Randomly permute the order of order types in the file.",
    )
    add_input_args(p)
    add_output_args(p, ".shuffled")
    p.set_defaults(func=_cmd_shuffle)


def _cmd_shuffle(args) -> None:
    ots = shuffle(open_input(args))
    out, fmt = resolve_output(args, ".shuffled.lt")
    write_order_types(ots, out, fmt=fmt)
    print(f"written: {len(ots)}  to: {out}")


# ---------------------------------------------------------------------------
# enum-sub-ot
# ---------------------------------------------------------------------------

def enum_sub_ot(
    ots: Iterable[SmallLambda],
    k: int,
    duplicates: bool = False,
) -> Iterator[SmallLambda]:
    """Yield all distinct k-point sub-order-types across all input OTs."""
    from pyotlib2.algorithms.sub_order_types import enumerate_sub_ots
    seen = set()
    for ot in ots:
        for sub in enumerate_sub_ots(ot, k, lex_min=not duplicates):
            key = sub.to_string()
            if duplicates or key not in seen:
                seen.add(key)
                yield sub


def _register_enum_subconf(sub) -> None:
    p = sub.add_parser(
        "enum-subconf",
        help="Enumerate k-point sub-configurations",
        description=(
            "Enumerate all distinct k-point sub-order-types appearing in "
            "the input.  Each k-element subset of points defines a sub-OT; "
            "duplicates are removed by lex-min normalization unless --duplicates is given."
        ),
    )
    add_input_args(p)
    add_output_args(p, ".sub-ot")
    p.add_argument("-k", type=int, required=True, help="Sub-order-type size")
    p.add_argument("--duplicates", action="store_true",
                   help="Include duplicates (no lex-min deduplication)")
    p.set_defaults(func=_cmd_enum_subconf)


def _cmd_enum_subconf(args) -> None:
    subs = list(enum_sub_ot(open_input(args), args.k, duplicates=args.duplicates))
    out, fmt = resolve_output(args, ".sub-ot.lt")
    write_order_types(subs, out, fmt=fmt)
    print(f"sub-ots: {len(subs)}  written to: {out}")


# ---------------------------------------------------------------------------
# count-sub-ot
# ---------------------------------------------------------------------------

def count_sub_ot(
    ots: Iterable[SmallLambda],
    k: int,
) -> Iterator[tuple]:
    """Yield (ot, count) of distinct k-point sub-order-types per OT."""
    from pyotlib2.algorithms.sub_order_types import count_distinct_sub_ots
    for ot in ots:
        yield ot, count_distinct_sub_ots(ot, k)


def _register_count_subconf(sub) -> None:
    p = sub.add_parser(
        "count-subconf",
        help="Count distinct k-point sub-configurations per OT",
        description=(
            "For each input order type, count the number of distinct k-point "
            "sub-order-types it contains.  Prints one count per line."
        ),
    )
    add_input_args(p)
    p.add_argument("-k", type=int, required=True, help="Sub-order-type size")
    p.set_defaults(func=_cmd_count_subconf)


def _cmd_count_subconf(args) -> None:
    max_cnt = 0
    for ot, cnt in count_sub_ot(open_input(args), args.k):
        max_cnt = max(max_cnt, cnt)
        print(cnt)
    print(f"max: {max_cnt}", file=sys.stderr)


# ---------------------------------------------------------------------------
# find-sub-ot
# ---------------------------------------------------------------------------

def find_sub_ot(
    ots: Iterable[SmallLambda],
    references: Iterable[SmallLambda],
    k: int,
) -> Iterator[tuple]:
    """Yield (ot, matched_ref_indices) for OTs containing reference sub-OTs."""
    from pyotlib2.algorithms.sub_order_types import find_sub_ots as _find
    refs = list(references)
    yield from _find(ots, refs, k)


def _register_find_subconf(sub) -> None:
    p = sub.add_parser(
        "find-subconf",
        help="Find OTs containing specific sub-configurations",
        description=(
            "Filter the input to order types that contain at least one of "
            "the reference k-point sub-order-types given in --ref.  "
            "Prints each matching OT together with which reference indices it contains."
        ),
    )
    add_input_args(p)
    p.add_argument("--ref", required=True, help="Reference OT file")
    p.add_argument("--ref-fmt", default=None)
    p.add_argument("--ref-n", type=int, default=None)
    p.add_argument("-k", type=int, required=True)
    p.set_defaults(func=_cmd_find_subconf)


def _cmd_find_subconf(args) -> None:
    refs = list(read_order_types(args.ref, fmt=args.ref_fmt, n=args.ref_n))
    for ot, matched in find_sub_ot(open_input(args), refs, args.k):
        print(ot.to_string().strip(), "->", matched)


# ---------------------------------------------------------------------------
# unify-pc
# ---------------------------------------------------------------------------

def unify_pc(ots: Iterable[SmallLambda]) -> Iterator[SmallLambda]:
    """Yield one PC representer per projective equivalence class."""
    from pyotlib2.algorithms.projective_class import ProjectiveClass
    seen = set()
    for ot in ots:
        pc = ProjectiveClass(ot)
        key = pc.representer.to_string()
        if key not in seen:
            seen.add(key)
            yield pc.representer


# _register_unify_pc removed — functionality merged into `unify --projective`


# ---------------------------------------------------------------------------
# lex-min-pc
# ---------------------------------------------------------------------------

def lex_min_pc(ots: Iterable[SmallLambda]) -> Iterator[SmallLambda]:
    """Relabel each OT to the PC representer of its projective class."""
    from pyotlib2.algorithms.projective_class import ProjectiveClass
    for ot in ots:
        yield ProjectiveClass(ot).representer


# _register_lex_min_pc removed — functionality merged into `lexmin --projective`


# ---------------------------------------------------------------------------
# enum-pc
# ---------------------------------------------------------------------------

def enum_pc(ots: Iterable[SmallLambda]) -> Iterator[SmallLambda]:
    """Yield all OTs in the projective class of each input OT."""
    from pyotlib2.algorithms.projective_class import ProjectiveClass
    seen_pcs = set()
    for ot in ots:
        pc = ProjectiveClass(ot)
        key = pc.representer.to_string()
        if key in seen_pcs:
            continue
        seen_pcs.add(key)
        yield from pc.all_ots()


def _register_enum_projective(sub) -> None:
    p = sub.add_parser(
        "enum-projective",
        help="Enumerate all OTs in each projective class",
        description=(
            "For each input order type, enumerate all order types in its "
            "projective class (rank-3 oriented matroid isomorphism class) "
            "via flip-graph BFS.  Duplicate PCs are skipped."
        ),
    )
    add_input_args(p)
    add_output_args(p, ".pc-full")
    p.set_defaults(func=_cmd_enum_projective)


def _cmd_enum_projective(args) -> None:
    ots = list(enum_pc(open_input(args)))
    out, fmt = resolve_output(args, ".pc-full.lt")
    write_order_types(ots, out, fmt=fmt)
    print(f"written: {len(ots)}  to: {out}")


# ---------------------------------------------------------------------------
# enum-natural  — enumerate all natural-labeled variants of each OT
# ---------------------------------------------------------------------------

def enum_natural(
    ots: Iterable[SmallLambda],
    mirror: bool = True,
) -> Iterator[SmallLambda]:
    """Yield all distinct natural-labeled variants of each input OT.

    For each hull point p0, the OT is relabeled so that p0 is first and
    the remaining points appear in CW angular order around p0.  If mirror
    is True, each variant is also mirrored (l-matrix transposed), doubling
    the candidate set.  Duplicates (same to_string()) are removed.

    The total number of distinct variants equals the size of the OT's
    symmetry group under natural-labeling equivalence.
    """
    for ot in ots:
        seen = set()
        for lab in ot.get_natural_labelings():
            if None in lab:
                continue
            variants = [ot.relabeled(lab)]
            if mirror:
                variants.append(variants[0].mirrored())
            for v in variants:
                key = v.to_string()
                if key not in seen:
                    seen.add(key)
                    yield v


def _register_enum_natural(sub) -> None:
    p = sub.add_parser(
        "enum-natural",
        help="Enumerate all natural-labeled variants of each OT",
        description=(
            "For each input order type, enumerate all distinct relabelings "
            "obtained by choosing each hull point as anchor p0 (natural labeling) "
            "and optionally mirroring.  "
            "This gives the orbit of the OT under the symmetry group of "
            "natural-labeling equivalence.  "
            "Use --no-mirror to suppress mirrored variants."
        ),
    )
    add_input_args(p)
    add_output_args(p, ".natural")
    p.add_argument("--no-mirror", action="store_false", dest="mirror", default=True,
                   help="Do not include mirrored variants")
    p.set_defaults(func=_cmd_enum_natural)


def _cmd_enum_natural(args) -> None:
    ots = list(enum_natural(open_input(args), mirror=args.mirror))
    out, fmt = resolve_output(args, ".natural.lt")
    write_order_types(ots, out, fmt=fmt)
    print(f"written: {len(ots)}  to: {out}")


# ---------------------------------------------------------------------------
# kgons
# ---------------------------------------------------------------------------

def kgons(
    ots: Iterable[SmallLambda],
    k: int,
    empty_only: bool = True,
) -> Iterator[tuple]:
    """Yield (ot, count) of empty/convex k-gons."""
    from pyotlib2.algorithms.polygon_count import count_polygons
    for ot in ots:
        bl = ot.to_big_lambda()
        yield ot, count_polygons(bl, k, empty_only=empty_only)


def _register_kgons(sub) -> None:
    p = sub.add_parser(
        "kgons",
        help="Count empty/convex k-gons",
        description=(
            "Count empty convex k-gons (k-holes) in each order type.  "
            "By default counts only empty k-gons (no interior points); "
            "use --convex to count all convex k-gons.  "
            "Use --enumerate to list the actual point index tuples."
        ),
    )
    add_input_args(p)
    p.add_argument("-k", type=int, required=True, help="Polygon size")
    p.add_argument("--convex", action="store_false", dest="empty_only",
                   help="Count all convex k-gons (not only empty ones)")
    p.add_argument("--enumerate", action="store_true",
                   help="Print each polygon found")
    p.set_defaults(func=_cmd_kgons, empty_only=True)


def _cmd_kgons(args) -> None:
    from pyotlib2.algorithms.polygon_count import enumerate_polygons, count_polygons
    for ot in open_input(args):
        bl = ot.to_big_lambda()
        if args.enumerate:
            for poly in enumerate_polygons(bl, args.k, empty_only=args.empty_only):
                print(poly)
        else:
            print(count_polygons(bl, args.k, empty_only=args.empty_only))


# ---------------------------------------------------------------------------
# properties
# ---------------------------------------------------------------------------

def properties(
    ots: Iterable[SmallLambda],
    props: list,
) -> Iterator[tuple]:
    """Yield (ot, {prop: value}) for each OT.

    Supported properties:
      crossings            rectilinear crossing number
      empty-triangles      number of empty triangles
      empty-kgons-K        number of empty convex K-gons  (e.g. empty-kgons-5)
      kgons-K              number of convex K-gons
      hull                 number of convex hull points
      onion-layers         number of convex layers
      triangulations       number of triangulations
    """
    from pyotlib2.algorithms.polygon_count import (
        count_polygons, count_crossings, count_triangles
    )
    for ot in ots:
        bl = ot.to_big_lambda()
        values = {}
        for prop in props:
            if prop == "crossings":
                values[prop] = count_crossings(ot)
            elif prop == "empty-triangles":
                values[prop] = count_triangles(bl, empty_only=True)
            elif prop.startswith("empty-kgons-"):
                k = int(prop.split("-")[-1])
                values[prop] = count_polygons(bl, k, empty_only=True)
            elif prop.startswith("kgons-"):
                k = int(prop.split("-")[-1])
                values[prop] = count_polygons(bl, k, empty_only=False)
            elif prop == "hull":
                values[prop] = len(ot.get_extremal_points())
            elif prop == "onion-layers":
                values[prop] = len(bl.get_onion())
            elif prop == "triangulations":
                from pyotlib2.algorithms.triangulations import count_triangulations
                values[prop] = count_triangulations(ot)
            else:
                raise ValueError(f"Unknown property: {prop!r}")
        yield ot, values


def _register_properties(sub) -> None:
    p = sub.add_parser(
        "properties",
        help="Compute combinatorial properties of order types",
        description=(
            "Compute one or more combinatorial properties for each order type "
            "and print them space-separated.  "
            "Available properties:\n"
            "  crossings       rectilinear crossing number\n"
            "  empty-triangles number of empty triangles\n"
            "  empty-kgons-K   number of empty convex K-gons (e.g. empty-kgons-5)\n"
            "  kgons-K         number of convex K-gons\n"
            "  hull            number of convex hull points\n"
            "  onion-layers    number of convex layers\n"
            "  triangulations  number of triangulations"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    add_input_args(p)
    p.add_argument("props", nargs="+", metavar="PROPERTY",
                   help="Properties: crossings, empty-triangles, empty-kgons-K, "
                        "kgons-K, hull, onion-layers, triangulations")
    p.set_defaults(func=_cmd_properties)


def _cmd_properties(args) -> None:
    for ot, values in properties(open_input(args), args.props):
        print(" ".join(str(values[p]) for p in args.props))


# ---------------------------------------------------------------------------
# realize
# ---------------------------------------------------------------------------

def realize(
    ots: Iterable[SmallLambda],
    method: str = "grid",
    trials: int = 20,
    gridsize: int = 256,
    grid_tries: int = 20,
    use_pc: bool = False,
    max_pc_trials: int = 0,
) -> Iterator[tuple]:
    """Test realizability of abstract order types.

    Yields (ot, result) where result is True/False/None (unknown).

    method: "grid" for randomized grid search (fast, good for small n);
            "scipy" for nonlinear optimization;
            "gp" for GLPK GP-LP (proves non-realizability).

    use_pc: if True, search through the projective class of each OT and test
            each member until one is realized or all (up to max_pc_trials) tried.
    """
    from pyotlib2.realization.base import Undecided

    if method == "gp":
        from pyotlib2.realization.gp_tester import GPRealizationTester
        tester = GPRealizationTester()
    elif method == "scipy":
        from pyotlib2.realization.scipy_tester import ScipyRealizationTester
        tester = ScipyRealizationTester(trials=trials)
    elif method == "grid":
        from pyotlib2.realization.grid_search import GridSearchTester
        tester = GridSearchTester(gridsize=gridsize, max_tries=grid_tries)
    else:
        raise ValueError(f"Unknown method: {method!r}")

    for ot in ots:
        if not use_pc:
            try:
                yield ot, tester.is_realizable(ot)
            except Undecided:
                yield ot, None
        else:
            from pyotlib2.algorithms.projective_class import ProjectiveClass
            pc = ProjectiveClass(ot)
            result = None
            it = 0
            for pc_ot in pc.all_ots():
                it += 1
                if max_pc_trials and it > max_pc_trials:
                    break
                try:
                    res = tester.is_realizable(pc_ot)
                    if res is True:
                        # attach realization back to original ot via pc transform
                        if pc_ot.realization is not None:
                            ot.realization = pc_ot.realization
                        result = True
                        break
                    elif res is False:
                        result = False
                        break
                except Undecided:
                    pass
            yield ot, result


def _register_realize(sub) -> None:
    p = sub.add_parser(
        "realize",
        help="Test realizability of order types",
        description=(
            "Test whether each abstract order type is realizable by a "
            "concrete point set.  "
            "Method 'grid' uses randomized backtracking on an integer grid (fast, good for small n); "
            "method 'scipy' uses nonlinear optimization; "
            "method 'gp' uses a Grassmann-Plücker LP via GLPK (proves non-realizability).  "
            "Use --pc to search through the projective class of each OT."
        ),
    )
    add_input_args(p)
    p.add_argument("--method", default="grid", choices=["grid", "scipy", "gp"],
                   help="Realization method (default: grid)")
    p.add_argument("--trials", type=int, default=20,
                   help="Number of optimization trials (scipy only)")
    p.add_argument("--gridsize", type=int, default=256,
                   help="Grid side length, power of 2 (grid method, default: 256)")
    p.add_argument("--grid-tries", type=int, default=20,
                   help="Independent restarts for grid search (default: 20)")
    p.add_argument("--pc", action="store_true", default=False,
                   help="Search through the projective class of each OT")
    p.add_argument("--max-pc-trials", type=int, default=0,
                   help="Max PC members to try per OT (0 = all, only with --pc)")
    p.set_defaults(func=_cmd_realize)


def _cmd_realize(args) -> None:
    results = {True: 0, False: 0, None: 0}
    for ot, res in realize(
        open_input(args),
        method=args.method,
        trials=args.trials,
        gridsize=args.gridsize,
        grid_tries=args.grid_tries,
        use_pc=args.pc,
        max_pc_trials=args.max_pc_trials,
    ):
        results[res] += 1
        tag = "realizable" if res is True else ("non-realizable" if res is False else "unknown")
        print(f"{tag}: {ot.to_string().strip()}")
    print(f"\nrealizable: {results[True]}  non-realizable: {results[False]}  unknown: {results[None]}")


# ---------------------------------------------------------------------------
# realize-pc  — search through projective class for a realization
# ---------------------------------------------------------------------------

def realize_pc(
    ots: Iterable[SmallLambda],
    method: str = "scipy",
    trials: int = 20,
    max_pc_trials: int = 0,
) -> Iterator[tuple]:
    """Test realizability by searching through the projective class.

    For each OT, iterates over OTs in its PC and tests each with the given
    method until one is realized or all (up to max_pc_trials) are exhausted.

    Yields (ot, result) where result is True/False/None.
    max_pc_trials=0 means try all OTs in the PC.
    """
    from pyotlib2.algorithms.projective_class import ProjectiveClass
    from pyotlib2.realization.base import Undecided

    if method == "gp":
        from pyotlib2.realization.gp_tester import GPRealizationTester
        tester = GPRealizationTester()
    elif method == "scipy":
        from pyotlib2.realization.scipy_tester import ScipyRealizationTester
        tester = ScipyRealizationTester(trials=trials)
    else:
        raise ValueError(f"Unknown method: {method!r}")

    for ot in ots:
        pc = ProjectiveClass(ot)
        result = None
        it = 0
        for pc_ot in pc.all_ots():
            it += 1
            if max_pc_trials and it > max_pc_trials:
                break
            try:
                res = tester.is_realizable(pc_ot)
                if res is True:
                    result = True
                    break
                elif res is False:
                    result = False
                    break
            except Undecided:
                pass
        yield ot, result


def _register_realize_pc(sub) -> None:
    p = sub.add_parser(
        "realize-pc",
        help="Test realizability by searching through the projective class",
        description=(
            "Test realizability by trying all order types in the projective class "
            "(rank-3 oriented matroid isomorphism class) of each input OT.  "
            "Succeeds as soon as any member of the PC is realized or proven non-realizable.  "
            "Use --max-pc-trials to limit how many PC members are tried."
        ),
    )
    add_input_args(p)
    p.add_argument("--method", default="scipy", choices=["scipy", "gp"])
    p.add_argument("--trials", type=int, default=20,
                   help="Optimization trials per OT (scipy only)")
    p.add_argument("--max-pc-trials", type=int, default=0,
                   help="Max OTs to try per PC (0 = all)")
    p.set_defaults(func=_cmd_realize_pc)


def _cmd_realize_pc(args) -> None:
    results = {True: 0, False: 0, None: 0}
    for ot, res in realize_pc(open_input(args), method=args.method,
                               trials=args.trials, max_pc_trials=args.max_pc_trials):
        results[res] += 1
        tag = "realizable" if res is True else ("non-realizable" if res is False else "unknown")
        print(f"{tag}: {ot.to_string().strip()}")
    print(f"\nrealizable: {results[True]}  non-realizable: {results[False]}  unknown: {results[None]}")


# ---------------------------------------------------------------------------
# smart-realize  — Etherealization: reduce point by point
# ---------------------------------------------------------------------------

def smart_realize(
    ot: SmallLambda,
    method: str = "scipy",
    trials: int = 20,
    use_pc: bool = True,
    max_pc_trials: int = 1,
) -> tuple[bool | None, SmallLambda | None]:
    """Try to realize an OT by iteratively adding one point at a time.

    Starts from the smallest sub-OT and grows by one point, using the
    previous realization as a warm start. If realization fails, tries
    to prove non-realizability of the smallest non-realizable sub-OT.

    Returns (result, witness) where:
      result=True  → witness is the realized OT (with realization)
      result=False → witness is the smallest non-realizable sub-OT found
      result=None  → undecided
    """
    from pyotlib2.realization.base import Undecided
    from pyotlib2.algorithms.projective_class import ProjectiveClass

    if method == "gp":
        from pyotlib2.realization.gp_tester import GPRealizationTester
        tester = GPRealizationTester()
    elif method == "scipy":
        from pyotlib2.realization.scipy_tester import ScipyRealizationTester
        tester = ScipyRealizationTester(trials=trials)
    else:
        raise ValueError(f"Unknown method: {method!r}")

    n = ot.n
    # build labeling: onion layers from outside in (last point = innermost)
    bl = ot.to_big_lambda()
    onion = bl.get_onion()
    labeling = []
    for layer in reversed(onion):
        labeling.extend(layer)
    # pad with any remaining points
    for i in range(n):
        if i not in labeling:
            labeling.append(i)

    def _try_realize(sub_ot):
        """Try direct + PC search."""
        try:
            res = tester.is_realizable(sub_ot)
            if res is not None:
                return res
        except Undecided:
            pass
        if use_pc:
            pc = ProjectiveClass(sub_ot)
            it = 0
            for pc_ot in pc.all_ots():
                it += 1
                if max_pc_trials and it > max_pc_trials:
                    break
                try:
                    res = tester.is_realizable(pc_ot)
                    if res is True:
                        return True
                    if res is False:
                        return False
                except Undecided:
                    pass
        return None

    # grow from sub-OT of size 3 up to n
    for size in range(3, n + 1):
        sub_indices = labeling[:size]
        sub_ot = ot.select_points(sub_indices)
        print(f"  n={size}: trying realization...", end=" ", flush=True)
        res = _try_realize(sub_ot)
        if res is True:
            print("realizable")
            if size == n:
                return True, sub_ot
        elif res is False:
            print("non-realizable")
            return False, sub_ot
        else:
            print("unknown")
            return None, sub_ot

    return None, None


def _register_smart_realize(sub) -> None:
    p = sub.add_parser(
        "smart-realize",
        help="Realize OT point-by-point (etherealization)",
        description=(
            "Attempt realization by growing the point set one point at a time "
            "(etherealization / onion-layer order).  "
            "Starts with a 3-point sub-OT and adds points one by one, "
            "testing realizability at each step.  "
            "If a sub-OT cannot be realized, the Grassmann-Plücker LP is used "
            "to try to certify non-realizability.  "
            "Optionally searches through the projective class at each step (--no-pc to disable)."
        ),
    )
    add_input_args(p)
    p.add_argument("--method", default="scipy", choices=["scipy", "gp"])
    p.add_argument("--trials", type=int, default=20)
    p.add_argument("--no-pc", action="store_false", dest="use_pc",
                   help="Don't search through projective class")
    p.add_argument("--max-pc-trials", type=int, default=1)
    p.set_defaults(func=_cmd_smart_realize, use_pc=True)


def _cmd_smart_realize(args) -> None:
    for ot in open_input(args):
        print(f"OT: {ot.to_string().strip()}")
        res, witness = smart_realize(ot, method=args.method, trials=args.trials,
                                     use_pc=args.use_pc, max_pc_trials=args.max_pc_trials)
        if res is True:
            print("  => realizable")
        elif res is False:
            print(f"  => non-realizable (smallest non-realizable sub-OT: {witness.to_string().strip()})")
        else:
            print("  => unknown")


# ---------------------------------------------------------------------------
# gp-test  — Grassmann-Plücker non-realizability test
# ---------------------------------------------------------------------------

def gp_test(ots: Iterable[SmallLambda]) -> Iterator[tuple]:
    """Test abstract order types for non-realizability using the GP-LP.

    Uses the Grassmann-Plücker linear program (via GLPK) to attempt to
    certify non-realizability.  A result of False means the OT is proven
    non-realizable.  A result of None means the test was inconclusive
    (the OT may or may not be realizable).

    Yields (ot, result) where result is False (non-realizable) or None (unknown).
    """
    from pyotlib2.realization.gp_tester import GPRealizationTester
    from pyotlib2.realization.base import Undecided
    tester = GPRealizationTester()
    for ot in ots:
        try:
            res = tester.is_realizable(ot)
            yield ot, res
        except Undecided:
            yield ot, None


def _register_gp_test(sub) -> None:
    p = sub.add_parser(
        "gp-test",
        help="Test non-realizability via Grassmann-Plücker LP",
        description=(
            "Attempt to certify non-realizability of abstract order types using "
            "the Grassmann-Plücker linear program (GP-LP) solved via GLPK.  "
            "A result of 'non-realizable' is a definitive proof.  "
            "'unknown' means the LP was inconclusive — the OT may still be "
            "realizable (use 'realize' to search for coordinates).  "
            "This is purely an abstract test: no coordinates are needed or produced."
        ),
    )
    add_input_args(p)
    p.set_defaults(func=_cmd_gp_test)


def _cmd_gp_test(args) -> None:
    results = {False: 0, None: 0}
    for ot, res in gp_test(open_input(args)):
        results[res] = results.get(res, 0) + 1
        tag = "non-realizable" if res is False else "unknown"
        print(f"{tag}: {ot.to_string().strip()}")
    print(f"\nnon-realizable: {results.get(False, 0)}  unknown: {results.get(None, 0)}")


# ---------------------------------------------------------------------------
# minimize-coords
# ---------------------------------------------------------------------------

def _require_realization(ot: SmallLambda, cmd: str) -> list:
    """Return realization coords or raise ValueError with helpful message."""
    if ot.realization is None:
        raise ValueError(
            f"OT has no realization — use a concrete input format "
            f"(b08, b16, asc, json) or run 'realize' first before '{cmd}'"
        )
    return list(ot.realization)


def _pts_get_bits(pts: list) -> int:
    return max((abs(v).bit_length() for p in pts for v in p), default=0)


def _pts_normalize(pts: list) -> list:
    """Translate so min x = min y = 0."""
    xmin = min(x for x, y in pts)
    ymin = min(y for x, y in pts)
    return [(x - xmin, y - ymin) for x, y in pts]


def _make_exit_validator(ot: SmallLambda):
    """Return a fast per-point validity checker using exit-edge triples."""
    from pyotlib2.algorithms.exit_edges import filter_exit_edges
    bl = ot.to_big_lambda()
    o = bl.o
    n = ot.n

    edges, witnesses = filter_exit_edges(ot, return_witnesses=True)

    # For each point i: list of (a, b, expected_sign) where (a,b) is an exit
    # edge with witness i, or i appears in the triple in any position.
    # We build combs[i] = list of (a, b, sign) to check when point i moves.
    combs: dict[int, list] = {i: [] for i in range(n)}
    for (a, b), ws in witnesses.items():
        for c in ws:
            sign = int(o[a, b, c])
            for idx in (a, b, c):
                combs[idx].append((a, b, c, sign))

    def is_valid(pts: list, i: int) -> bool:
        xi, yi = pts[i]
        for a, b, c, expected in combs[i]:
            xa, ya = pts[a]
            xb, yb = pts[b]
            xc, yc = pts[c]
            det = xa * (yb - yc) + xb * (yc - ya) + xc * (ya - yb)
            if expected > 0 and det <= 0:
                return False
            if expected < 0 and det >= 0:
                return False
        return True

    return is_valid


# ---------------------------------------------------------------------------
# minimize-coords
# ---------------------------------------------------------------------------

def minimize_coords(
    ot: SmallLambda,
    trials: int = 10,
    randomize: int = 10,
    tolerance: int = 0,
    sheering: bool = False,
) -> SmallLambda:
    """Minimize the coordinate size of a realized order type.

    Algorithm (ported from old pyotlib minimizeIntegerCoordinates):
      - Phase 1: move each point to even coordinates (4 candidate offsets)
      - Phase 2A: if all points could be made even, halve all coordinates
      - Phase 2B: if some point resists, randomize with Gaussian-like jumps
      - Mid-run blow-up (×3) if no improvement after trials/2 attempts
      - Optionally try sheering transforms x←x+y, y←y+x beforehand

    Only exit-edge triples are checked for orientation (O(n) per point
    instead of O(n²)), making this fast for large n.

    Requires ot.realization to be set.
    """
    import random
    from copy import copy

    pts = _require_realization(ot, "minimize-coords")
    n = ot.n
    is_valid = _make_exit_validator(ot)

    def get_bits(p):
        return _pts_get_bits(p)

    def move_to_even(pts, i):
        x, y = p0 = pts[i]
        if x % 2 == 0 and y % 2 == 0:
            return True
        for nx, ny in [
            (x + x % 2, y + y % 2),
            (x - x % 2, y + y % 2),
            (x + x % 2, y - y % 2),
            (x - x % 2, y - y % 2),
        ]:
            pts[i] = (nx, ny)
            if is_valid(pts, i):
                return True
        pts[i] = p0
        return False

    def randomize_point(pts, i, bits):
        x, y = p0 = pts[i]
        for e in range(bits, 0, -1):
            M = 2 ** e
            for _ in range(10):
                pts[i] = (x + random.randint(-M, M), y + random.randint(-M, M))
                if is_valid(pts, i):
                    return
        pts[i] = p0

    def balance(pts):
        """Scale axes so both have same range (improves convergence)."""
        xs = [x for x, y in pts]
        ys = [y for x, y in pts]
        xr = max(xs) - min(xs) or 1
        yr = max(ys) - min(ys) or 1
        mx = max(1, yr // xr)
        my = max(1, xr // yr)
        return [(x * mx, y * my) for x, y in pts]

    def run_minimize(pts):
        pts = _pts_normalize(pts)
        pts = balance(pts)
        best_pts = copy(pts)
        best_bits = get_bits(pts)
        it = 0
        while it < trials:
            ok = all(move_to_even(pts, i) for i in range(n))
            if ok:
                pts = [(x // 2, y // 2) for x, y in _pts_normalize(pts)]
                bits = get_bits(pts)
                if bits < best_bits:
                    best_bits = bits
                    best_pts = copy(pts)
                    it = 0
                    if tolerance and best_bits <= tolerance:
                        break
            else:
                bits = get_bits(pts)
                for _ in range(randomize):
                    for i in range(n):
                        randomize_point(pts, i, random.randint(0, max(1, bits)))
                it += 1
                if it == trials // 2:
                    # blow-up: scale ×3 to escape local minimum
                    pts = _pts_normalize(pts)
                    pts = balance([(x * 3, y * 3) for x, y in pts])
        return best_pts, best_bits

    # try plain + optional sheering variants
    candidates = [pts]
    if sheering:
        candidates += [
            [(x + y, y) for x, y in pts],
            [(x, y + x) for x, y in pts],
            [(x - y, y) for x, y in pts],
            [(x, y - x) for x, y in pts],
        ]

    best_pts = pts
    best_bits = _pts_get_bits(pts)
    for cand in candidates:
        p, b = run_minimize(list(cand))
        if b < best_bits:
            best_bits = b
            best_pts = p
        if tolerance and best_bits <= tolerance:
            break

    best_pts = _pts_normalize(best_pts)
    from pyotlib2.core.small_lambda import SmallLambda as SL
    result = SL(n, ot.get_l().copy(), realization=best_pts)
    return result


def _register_minimize_coords(sub) -> None:
    p = sub.add_parser(
        "minimize-coords",
        help="Minimize coordinate size of realized order types",
        description=(
            "Reduce the bit-width of the coordinates of a concrete point set "
            "realization while preserving the order type.  Uses the "
            "move-to-even / halve algorithm with randomized restarts and a "
            "mid-run blow-up.  Only exit-edge triples are checked per move "
            "(fast).  Optionally tries sheering transforms (x←x+y etc.) for "
            "better results.  Input must be a concrete format (b08/b16/asc/json)."
        ),
    )
    add_input_args(p)
    add_output_args(p, ".min")
    p.add_argument("--trials", type=int, default=10,
                   help="Iteration budget (default: 10)")
    p.add_argument("--randomize", type=int, default=10,
                   help="Randomization rounds per failed phase (default: 10)")
    p.add_argument("--tolerance", type=int, default=0,
                   help="Stop when bits ≤ tolerance (default: 0 = minimize fully)")
    p.add_argument("--sheering", action="store_true",
                   help="Also try sheering transforms (x←x+y, y←y+x, …)")
    p.set_defaults(func=_cmd_minimize_coords)


def _cmd_minimize_coords(args) -> None:
    written = 0
    out, fmt = resolve_output(args, ".min.lt")
    results = []
    for ot in open_input(args):
        try:
            result = minimize_coords(
                ot,
                trials=args.trials,
                randomize=args.randomize,
                tolerance=args.tolerance,
                sheering=args.sheering,
            )
            b0 = _pts_get_bits(list(ot.realization)) if ot.realization else "?"
            b1 = _pts_get_bits(result.realization)
            print(f"bits: {b0} → {b1}")
            results.append(result)
            written += 1
        except ValueError as e:
            print(f"skip: {e}", file=sys.stderr)
    write_order_types(results, out, fmt=fmt)
    print(f"written: {written}  to: {out}")


# ---------------------------------------------------------------------------
# beautify-coords  — gradient descent via binary search on each coordinate
# ---------------------------------------------------------------------------

def beautify_coords(
    ot: SmallLambda,
    max_iter: int = 100,
    good_bits: int = 0,
) -> SmallLambda:
    """Beautify coordinates via gradient descent with binary search.

    For each coordinate, binary-searches the largest safe range [zl, zu]
    and moves to the midpoint.  Converges towards a "centred" realization
    with smaller spread.  Runs for at most max_iter iterations or until
    convergence.

    If good_bits > current bits, the point set is scaled up first so that
    scipy has more room to work.

    Ported from old pyotlib PointSetOptimizer.beautifyPointSet.
    Requires ot.realization to be set.
    """
    from fractions import Fraction
    from copy import copy

    pts = _require_realization(ot, "beautify-coords")
    n = ot.n
    pts = _pts_normalize(pts)
    cur_bits = _pts_get_bits(pts)

    # scale up if requested
    if good_bits and cur_bits < good_bits:
        scale = 2 ** (good_bits - cur_bits)
        pts = [(x * scale, y * scale) for x, y in pts]
        cur_bits = good_bits

    # build orientation lookup: only positive-oriented triples (a<b, a<c)
    bl = ot.to_big_lambda()
    o = bl.o
    orientations = [
        (a, b, c)
        for a in range(n) for b in range(n) for c in range(n)
        if a < b and a < c and int(o[a, b, c]) > 0
    ]
    # per-coordinate index: orientations involving coordinate i (x) or i+n (y)
    ori_by_coord = {k: [] for k in range(2 * n)}
    for a, b, c in orientations:
        for idx in (a, b, c):
            ori_by_coord[idx].append((a, b, c))
            ori_by_coord[idx + n].append((a, b, c))

    # Z = [x0, x1, ..., x_{n-1}, y0, y1, ..., y_{n-1}]
    Z = [x for x, y in pts] + [y for x, y in pts]

    def o3(Z, a, b, c):
        return (Z[a] * Z[b + n] - Z[a + n] * Z[b]
                + Z[b] * Z[c + n] - Z[b + n] * Z[c]
                + Z[c] * Z[a + n] - Z[c + n] * Z[a])

    def is_valid_coord(Z, coord):
        for a, b, c in ori_by_coord[coord]:
            if o3(Z, a, b, c) < 1:
                return False
        return True

    ot_str = ot.to_string()
    min_diff = 2 * n * 2 ** cur_bits
    stop_timer = 5

    for it in range(1, max_iter + 1):
        Z0 = copy(Z)
        grad = []

        for coord in range(2 * n):
            z0 = Z[coord]
            zl = zu = z0
            for bit in reversed(range(cur_bits + 1)):
                Z[coord] = zl - 2 ** bit
                if is_valid_coord(Z, coord):
                    zl = Z[coord]
                Z[coord] = zu + 2 ** bit
                if is_valid_coord(Z, coord):
                    zu = Z[coord]
            Z[coord] = z0
            grad.append((zl + zu) // 2 - z0)

        convergence = Fraction(10, 10 + it)
        grad_f = [g * convergence for g in grad]

        factor = Fraction(1)
        # backtrack until valid
        while factor > Fraction(1, 2 ** 20):
            for k in range(2 * n):
                Z[k] = Z0[k] + int(factor * grad_f[k])
            if all(o3(Z, a, b, c) > 0 for a, b, c in orientations):
                break
            factor /= 2
        else:
            Z = Z0
            break

        # try to extrapolate further (cap at 2^20 to avoid infinite loop when grad=0)
        df = Fraction(10, 9)
        while factor < Fraction(2 ** 20):
            factor *= df
            for k in range(2 * n):
                Z[k] = Z0[k] + int(factor * grad_f[k])
            if not all(o3(Z, a, b, c) > 0 for a, b, c in orientations):
                factor /= df
                break
        if factor > 1:
            factor = Fraction(1)
        for k in range(2 * n):
            Z[k] = Z0[k] + int(factor * grad_f[k])

        diffs = sum(abs(Z[k] - Z0[k]) for k in range(2 * n))
        if diffs < min_diff:
            min_diff = diffs
        else:
            stop_timer = 8
        stop_timer -= 1
        if diffs == 0 or stop_timer < 0:
            break

    # reconstruct point set
    new_pts = list(zip(Z[:n], Z[n:]))
    new_pts = _pts_normalize(new_pts)
    from pyotlib2.core.point_set import PointSet
    ps = PointSet(n, new_pts)
    if ps.to_small_lambda().to_string() == ot_str:
        from pyotlib2.core.small_lambda import SmallLambda as SL
        return SL(n, ot.get_l().copy(), realization=new_pts)
    # fallback: return original
    return ot


def _register_beautify_coords(sub) -> None:
    p = sub.add_parser(
        "beautify-coords",
        help="Beautify coordinates via gradient descent or Nelder-Mead",
        description=(
            "Optimize point set coordinates while preserving the order type.\n\n"
            "  --method gd  (default) Binary-search gradient descent: for each\n"
            "               coordinate, find the largest safe range and move to\n"
            "               its midpoint.  Fast, no external dependencies.\n\n"
            "  --method nm  Nelder-Mead simplex (scipy): minimizes a quality\n"
            "               function over exit-edge constraints and spread.\n"
            "               Convex hull points are fixed; result is rounded to\n"
            "               integers after each outer iteration.\n\n"
            "Input must be a concrete format (b08/b16/asc/json)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    add_input_args(p)
    add_output_args(p, ".beauty")
    p.add_argument("--method", choices=["gd", "nm"], default="gd",
                   help="Optimization method: gd=gradient descent, nm=Nelder-Mead (default: gd)")
    p.add_argument("--max-iter", type=int, default=100,
                   help="Max iterations for gd (default: 100)")
    p.add_argument("--iter1", type=int, default=5,
                   help="Outer iterations for nm (default: 5)")
    p.add_argument("--iter2", type=int, default=2000,
                   help="Max scipy evaluations per outer iter for nm (default: 2000)")
    p.add_argument("--good-bits", type=int, default=0,
                   help="Scale up to this bit-width before optimizing (default: 0 = no scale)")
    p.add_argument("--no-minimize", action="store_false", dest="minimize",
                   help="(nm only) Skip minimize-coords after each scipy run")
    p.add_argument("--norm", type=int, default=1,
                   help="(nm only) Lp norm for quality function (default: 1)")
    p.add_argument("--epsilon", type=float, default=1e-4,
                   help="(nm only) scipy convergence tolerance (default: 1e-4)")
    p.set_defaults(func=_cmd_beautify_coords, minimize=True)


def _cmd_beautify_coords(args) -> None:
    written = 0
    out, fmt = resolve_output(args, ".beauty.lt")
    results = []
    for ot in open_input(args):
        try:
            if args.method == "gd":
                result = beautify_coords(ot, max_iter=args.max_iter, good_bits=args.good_bits)
            else:
                result = beautify2_coords(
                    ot,
                    iter1=args.iter1,
                    iter2=args.iter2,
                    good_bits=args.good_bits,
                    minimize=args.minimize,
                    norm=args.norm,
                    epsilon=args.epsilon,
                )
            b0 = _pts_get_bits(list(ot.realization)) if ot.realization else "?"
            b1 = _pts_get_bits(result.realization)
            print(f"bits: {b0} → {b1}")
            results.append(result)
            written += 1
        except ValueError as e:
            print(f"skip: {e}", file=sys.stderr)
    write_order_types(results, out, fmt=fmt)
    print(f"written: {written}  to: {out}")


# ---------------------------------------------------------------------------
# beautify2-coords  — scipy Nelder-Mead with exit-edge constraint function
# ---------------------------------------------------------------------------

def beautify2_coords(
    ot: SmallLambda,
    iter1: int = 5,
    iter2: int = 2000,
    good_bits: int = 0,
    minimize: bool = True,
    norm: int = 1,
    epsilon: float = 1e-4,
) -> SmallLambda:
    """Beautify coordinates using scipy Nelder-Mead optimization.

    Quality function (minimized):
      error1 = (Σ 1/[o3(a,b,c)·sign / perimeter]^norm)^(1/norm)  [constraint]
      error2 = (Σ d²·Σ 1/d²)^(1/norm)                             [spread]
      error3 = |log(max|coord|)|                                    [scale]
      error  = error1 · error2 · error3

    Only exit-edge triples are used for error1 (much cheaper than all C(n,3)).
    Convex hull points are fixed during scipy optimization.
    After each scipy run the result is rounded to integers.
    Optionally followed by minimize_coords.

    Ported from old pyotlib PointSetOptimizer.beautify2.
    Requires ot.realization to be set.
    """
    import math
    from copy import copy

    try:
        import scipy.optimize
    except ImportError:
        raise RuntimeError("scipy is required for beautify2-coords: pip install scipy")

    pts = _require_realization(ot, "beautify2-coords")
    n = ot.n
    pts = _pts_normalize(pts)
    ot_str = ot.to_string()

    bl = ot.to_big_lambda()
    o = bl.o

    from pyotlib2.algorithms.exit_edges import filter_exit_edges
    edges, witnesses = filter_exit_edges(ot, return_witnesses=True)
    exit_trps = [(a, b, c) for (a, b), ws in witnesses.items() for c in ws]

    hull = ot.get_extremal_points()

    cur_bits = _pts_get_bits(pts)
    if good_bits and cur_bits < good_bits:
        scale = 2 ** (good_bits - cur_bits)
        pts = [(x * scale, y * scale) for x, y in pts]

    def quality(Z):
        # fix hull points
        for i in hull:
            Z[i] = Z0[i]
            Z[i + n] = Z0[i + n]
        X = Z[:n]
        Y = Z[n:]
        zmax = max(abs(z) for z in Z) or 1

        def o3(a, b, c):
            return (X[a] * Y[b] - Y[a] * X[b]
                    + X[b] * Y[c] - Y[b] * X[c]
                    + X[c] * Y[a] - Y[c] * X[a])

        def d2(a, b):
            return (X[a] - X[b]) ** 2 + (Y[a] - Y[b]) ** 2

        def perim(a, b, c):
            return math.sqrt(d2(a, b)) + math.sqrt(d2(b, c)) + math.sqrt(d2(c, a))

        F3 = []
        for a, b, c in exit_trps:
            sign = int(o[a, b, c])
            p = perim(a, b, c)
            v = sign * o3(a, b, c) / p if p > 0 else 0
            F3.append(v)

        if not F3 or min(F3) <= 0:
            return float("inf")

        D2 = [d2(a, b) for a in range(n) for b in range(a + 1, n)]
        if not D2 or min(D2) <= 0:
            return float("inf")

        error1 = sum(1.0 / v ** norm for v in F3) ** (1.0 / norm)
        error2 = (sum(v ** norm for v in D2) * sum(1.0 / v ** norm for v in D2)) ** (1.0 / norm)
        error3 = abs(math.log(zmax))
        return error1 * error2 * (error3 + 1e-9)

    def to_integer(Z):
        scale = max(abs(z) for z in Z) or 1
        factor = 2 ** 20 / scale
        return [int(round(z * factor)) for z in Z]

    for _it in range(iter1):
        X0, Y0 = zip(*pts)
        Z0 = list(X0) + list(Y0)

        sol = scipy.optimize.fmin(
            quality, Z0,
            xtol=epsilon, ftol=epsilon,
            maxiter=iter2, maxfun=50 * iter2,
            disp=False,
        )
        # restore hull
        for i in hull:
            sol[i] = Z0[i]
            sol[i + n] = Z0[i + n]

        Zi = to_integer(list(sol))
        new_pts = list(zip(Zi[:n], Zi[n:]))
        new_pts = _pts_normalize(new_pts)

        # verify OT preserved
        from pyotlib2.core.point_set import PointSet
        ps = PointSet(n, new_pts)
        if ps.to_small_lambda().to_string() == ot_str:
            pts = new_pts
            if minimize:
                from pyotlib2.core.small_lambda import SmallLambda as SL
                tmp = SL(n, ot.get_l().copy(), realization=pts)
                tmp = minimize_coords(tmp, trials=10, randomize=10)
                pts = list(tmp.realization)

    from pyotlib2.core.small_lambda import SmallLambda as SL
    final_pts = _pts_normalize(pts)
    ps = PointSet(n, final_pts)
    if ps.to_small_lambda().to_string() == ot_str:
        return SL(n, ot.get_l().copy(), realization=final_pts)
    return ot  # fallback




# ---------------------------------------------------------------------------
# plot  — visualize order types as point set drawings
# ---------------------------------------------------------------------------

def plot_ot(
    ot: SmallLambda,
    ax,
    *,
    title: Optional[str] = None,
    labels: bool = True,
    hull: bool = True,
    edges: bool = False,
    crossings: bool = False,
    point_size: int = 60,
) -> None:
    """Draw a single order type on a matplotlib Axes.

    If ot has a concrete realization it is used directly; otherwise a
    realization is computed via scipy (raises ValueError if it fails).

    Parameters
    ----------
    ot:         order type to draw
    ax:         matplotlib Axes to draw on
    title:      optional title string
    labels:     whether to annotate points with their index
    hull:       whether to draw the convex hull polygon
    edges:      whether to draw all n*(n-1)/2 connecting segments
    crossings:  highlight crossing pairs of segments (implies edges=True)
    point_size: scatter marker size
    """
    try:
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
        from matplotlib.collections import LineCollection
    except ImportError:
        raise RuntimeError(
            "matplotlib is required for plotting.\n"
            "Install with:  pip install 'pyotlib2[vis]'"
        )

    # --- get coordinates ---
    pts = ot.realization
    if pts is None:
        raise ValueError(
            "OT has no coordinates — use a concrete input format (b08, b16, asc, json)"
        )

    xs = [float(x) for x, y in pts]
    ys = [float(y) for x, y in pts]
    n = ot.n

    # --- normalize to [0,1]² for stable display ---
    xlo, xhi = min(xs), max(xs)
    ylo, yhi = min(ys), max(ys)
    span = max(xhi - xlo, yhi - ylo) or 1.0
    margin = 0.12 * span
    xs_n = [(x - xlo) / span for x in xs]
    ys_n = [(y - ylo) / span for y in ys]

    bl = ot.to_big_lambda()

    # --- all edges (optional) ---
    if edges or crossings:
        segs = [((xs_n[i], ys_n[i]), (xs_n[j], ys_n[j]))
                for i in range(n) for j in range(i + 1, n)]
        if crossings:
            cross_pairs = set()
            for i in range(n):
                for j in range(i + 1, n):
                    for k in range(n):
                        for l in range(k + 1, n):
                            if len({i, j, k, l}) == 4 and bl.edges_cross((i, j), (k, l)):
                                cross_pairs.add((min(i,j), max(i,j)))
                                cross_pairs.add((min(k,l), max(k,l)))
            colors = [
                "#e74c3c" if (min(i,j), max(i,j)) in cross_pairs else "#bdc3c7"
                for i in range(n) for j in range(i + 1, n)
            ]
            lc = LineCollection(segs, colors=colors, linewidths=0.8, zorder=1)
        else:
            lc = LineCollection(segs, colors="#bdc3c7", linewidths=0.8, zorder=1)
        ax.add_collection(lc)

    # --- convex hull polygon ---
    if hull:
        hull_pts = ot.get_extremal_points()
        # order hull points by angle around centroid
        cx = sum(xs_n[i] for i in hull_pts) / len(hull_pts)
        cy = sum(ys_n[i] for i in hull_pts) / len(hull_pts)
        import math
        hull_pts_sorted = sorted(hull_pts,
                                 key=lambda i: math.atan2(ys_n[i] - cy, xs_n[i] - cx))
        hx = [xs_n[i] for i in hull_pts_sorted] + [xs_n[hull_pts_sorted[0]]]
        hy = [ys_n[i] for i in hull_pts_sorted] + [ys_n[hull_pts_sorted[0]]]
        ax.fill(hx, hy, alpha=0.08, color="#3498db", zorder=0)
        ax.plot(hx, hy, color="#3498db", linewidth=1.2, zorder=2)

    # --- points ---
    ax.scatter(xs_n, ys_n, s=point_size, color="#2c3e50", zorder=3)

    # --- labels ---
    if labels:
        offset = 0.04
        for i, (x, y) in enumerate(zip(xs_n, ys_n)):
            ax.annotate(
                str(i),
                (x, y),
                xytext=(x + offset, y + offset),
                fontsize=8,
                color="#2c3e50",
                zorder=4,
            )

    ax.set_aspect("equal")
    ax.set_xlim(-0.1, 1.1)
    ax.set_ylim(-0.1, 1.1)
    ax.axis("off")
    if title:
        ax.set_title(title, fontsize=9, pad=4)


def plot(
    ots: Iterable[SmallLambda],
    output: Optional[str] = None,
    *,
    cols: int = 4,
    labels: bool = True,
    hull: bool = True,
    edges: bool = False,
    crossings: bool = False,
    point_size: int = 60,
    dpi: int = 150,
) -> None:
    """Plot order types as point set drawings.

    Arranges multiple OTs in a grid.  If output is None, opens an
    interactive matplotlib window.

    Parameters
    ----------
    ots:        iterable of order types
    output:     file path to save (png/pdf/svg/…); None → interactive
    cols:       number of columns in the grid
    labels:     annotate points with their index
    hull:       draw convex hull polygon
    edges:      draw all connecting segments
    crossings:  highlight crossing segment pairs (implies edges)
    point_size: scatter marker size
    dpi:        output resolution (for raster formats)
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        raise RuntimeError(
            "matplotlib is required for plotting.\n"
            "Install with:  pip install 'pyotlib2[vis]'"
        )
    import math

    ot_list = list(ots)
    if not ot_list:
        print("no order types to plot", file=sys.stderr)
        return

    n_ots = len(ot_list)
    ncols = min(cols, n_ots)
    nrows = math.ceil(n_ots / ncols)
    fig_w = 2.5 * ncols
    fig_h = 2.5 * nrows

    fig, axes = plt.subplots(nrows, ncols, figsize=(fig_w, fig_h),
                              squeeze=False)
    fig.patch.set_facecolor("white")

    for idx, ot in enumerate(ot_list):
        r, c = divmod(idx, ncols)
        ax = axes[r][c]
        title = f"OT {idx+1}  (n={ot.n})"
        try:
            plot_ot(ot, ax, title=title, labels=labels, hull=hull,
                    edges=edges, crossings=crossings, point_size=point_size)
        except ValueError as e:
            ax.text(0.5, 0.5, f"[no realization]\n{e}",
                    ha="center", va="center", fontsize=7, color="gray",
                    transform=ax.transAxes)
            ax.set_title(title, fontsize=9, pad=4)
            ax.axis("off")

    # hide unused axes
    for idx in range(n_ots, nrows * ncols):
        r, c = divmod(idx, ncols)
        axes[r][c].set_visible(False)

    plt.tight_layout(pad=0.5)

    if output:
        plt.savefig(output, dpi=dpi, bbox_inches="tight")
        print(f"saved: {output}")
    else:
        plt.show()
    plt.close(fig)


def _register_plot(sub) -> None:
    p = sub.add_parser(
        "plot",
        help="Visualize order types as point set drawings",
        description=(
            "Plot order types as 2D point set drawings using matplotlib.  "
            "Requires a concrete input format with coordinates: b08, b16, asc, json.  "
            "Abstract formats (lt, blt) are not supported — realization is a hard problem.  "
            "Without -o, an interactive window is opened."
        ),
    )
    add_input_args(p)
    p.add_argument("-o", "--output", default=None,
                   help="Output file (png, pdf, svg, …). Default: interactive window.")
    p.add_argument("--cols", type=int, default=4,
                   help="Number of columns in the plot grid (default: 4)")
    p.add_argument("--no-labels", action="store_false", dest="labels",
                   help="Don't annotate points with their index")
    p.add_argument("--no-hull", action="store_false", dest="hull",
                   help="Don't draw the convex hull")
    p.add_argument("--edges", action="store_true",
                   help="Draw all connecting segments between points")
    p.add_argument("--crossings", action="store_true",
                   help="Highlight crossing segment pairs (implies --edges)")
    p.add_argument("--point-size", type=int, default=60,
                   help="Scatter marker size (default: 60)")
    p.add_argument("--dpi", type=int, default=150,
                   help="Output resolution for raster formats (default: 150)")
    p.set_defaults(func=_cmd_plot, labels=True, hull=True)


def _cmd_plot(args) -> None:
    plot(
        open_input(args),
        output=args.output,
        cols=args.cols,
        labels=args.labels,
        hull=args.hull,
        edges=args.edges,
        crossings=args.crossings,
        point_size=args.point_size,
        dpi=args.dpi,
    )


# ---------------------------------------------------------------------------
# editor  — interactive PySide6 point set editor
# ---------------------------------------------------------------------------

def _register_editor(sub) -> None:
    p = sub.add_parser(
        "editor",
        help="Interactive point set editor (requires PySide6)",
        description=(
            "Open an interactive editor to drag points and explore order types.  "
            "Requires PySide6:  pip install -e '.[vis]'  "
            "With a file argument, loads the first order type from that file "
            "(must have concrete coordinates: b08, b16, asc, json).  "
            "Without a file, opens a default 6-point convex configuration."
        ),
    )
    p.add_argument("file", nargs="?", default=None,
                   help="Input file with point coordinates (optional)")
    p.add_argument("-n", dest="n", type=int, default=None,
                   help="Number of points (required for binary formats)")
    p.add_argument("--fmt", default=None,
                   help="File format (auto-detected from extension if omitted)")
    p.set_defaults(func=_cmd_editor)


def _cmd_editor(args) -> None:
    try:
        from pyotlib2.vis.editor.app import run_editor
    except ImportError:
        import sys
        print(
            "Error: PySide6 is required for the editor.\n"
            "Install with:  pip install -e '.[vis]'",
            file=sys.stderr,
        )
        sys.exit(1)
    run_editor(args.file, n=args.n, fmt=args.fmt)


# ===========================================================================
# Shared helper: property counting by name
# ===========================================================================

_PROP_HELP = (
    "  crossings        rectilinear crossing number\n"
    "  empty-triangles  number of empty triangles\n"
    "  empty-kgons-K    number of empty convex K-gons (e.g. empty-kgons-5)\n"
    "  kgons-K          number of convex K-gons\n"
    "  hull             number of convex hull points\n"
    "  onion-layers     number of convex layers"
)


def _count_property(ot: SmallLambda, prop: str) -> int:
    """Count a single named property on an order type."""
    from pyotlib2.algorithms.polygon_count import (
        count_polygons, count_crossings, count_empty_kgons,
    )
    if prop == "crossings":
        return count_crossings(ot)
    elif prop == "hull":
        return len(ot.get_extremal_points())
    elif prop == "onion-layers":
        return len(ot.big_lambda.get_onion())
    elif prop == "empty-triangles":
        return count_empty_kgons(ot, k=3)
    elif prop.startswith("empty-kgons-"):
        k = int(prop.removeprefix("empty-kgons-"))
        return count_empty_kgons(ot, k)
    elif prop.startswith("kgons-"):
        k = int(prop.removeprefix("kgons-"))
        return count_polygons(ot.big_lambda, k, empty_only=False)
    else:
        raise ValueError(f"Unknown property: {prop!r}. Available:\n{_PROP_HELP}")


def _output_path(input_path: str, suffix: str, index: int = 0) -> str:
    """Build output path: input.suffix or input.suffix.001 input.suffix.002 ..."""
    from pathlib import Path
    base = str(Path(input_path).with_suffix("")) + suffix
    if index == 0:
        return base
    return f"{base}.{index:03d}"


# ===========================================================================
# walk-points  — local search in coordinate space (DFS or random)
# ===========================================================================

def walk_points(
    ot: SmallLambda,
    prop: str,
    *,
    random_walk: bool = False,
    trials: int = 0,
    walk_range: int = 0,
    trace: int = 10000,
    good_bits: int = 30,
    max_steps: int = 0,
    stop_if_improved: bool = False,
    siman: bool = False,
    T0: float = 0.1,
    dT: float = 0.999,
    verbose: bool = True,
) -> Iterator[SmallLambda]:
    """Local search in coordinate space to minimize a property.

    Two modes (selected via random_walk):

    DFS mode (random_walk=False):
        For each configuration on the stack: try moving each point in 16
        rational directions via binary search to the OT boundary, then step
        one unit past it to reach a neighboring OT.  Each unseen neighbor
        is pushed onto the DFS stack.

    Random mode (random_walk=True):
        At each step pick a random point and move it by a random offset in
        [-walk_range, +walk_range]².  Accept if the property does not
        increase (greedy descent, no backtracking).

    Both modes yield each strictly improving OT found.
    Requires ot.realization to be set.
    """
    import collections
    import hashlib
    import random
    from math import exp
    from pyotlib2.core.point_set import PointSet

    pts = _require_realization(ot, "walk-points")
    n = ot.n

    # scale up for numerical stability (DFS mode)
    cur_bits = _pts_get_bits(pts)
    if not random_walk and good_bits and cur_bits < good_bits:
        scale = 2 ** (good_bits - cur_bits)
        pts = [(x * scale, y * scale) for x, y in pts]
    pts = _pts_normalize(pts)

    start_count = _count_property(PointSet(n, pts).to_small_lambda(), prop)
    min_count = start_count
    temperature = T0

    if verbose:
        print(f"start: {prop}={start_count}")

    # ---- random walk mode ----
    if random_walk:
        if walk_range <= 0:
            diam = max(abs(x) for x, y in pts) + max(abs(y) for x, y in pts)
            walk_range = 5 + diam // 3
        if verbose:
            print(f"  range={walk_range}")

        _trial = 0
        while trials == 0 or _trial < trials:
            _trial += 1
            i = random.randrange(n)
            x, y = pts[i]
            dx = random.randint(-walk_range, walk_range)
            dy = random.randint(-walk_range, walk_range)
            pts[i] = (x + dx, y + dy)

            if len(set(pts)) < n:
                pts[i] = (x, y)
                continue
            ps = PointSet(n, pts)
            if ps.has_collinear_points():
                pts[i] = (x, y)
                continue

            new_ot = ps.to_small_lambda()
            new_count = _count_property(new_ot, prop)

            if new_count > min_count:
                pts[i] = (x, y)
                continue

            if new_count < min_count:
                min_count = new_count
                pts = _pts_normalize(pts)
                if verbose:
                    print(f"  improved: {prop}={min_count}")
                yield new_ot
                if stop_if_improved:
                    return
            # equal: keep the move
        return

    # ---- DFS mode ----
    directions = set()
    for k, l in [(1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (1, 6)]:
        for dk, dl in [(k, l), (l, k), (-l, k), (-k, l),
                       (-k, -l), (-l, -k), (l, -k), (k, -l)]:
            directions.add((dk, dl))
    directions = list(directions)

    def ot_key(pts):
        return hashlib.md5(PointSet(n, pts).to_small_lambda().to_string().encode()).hexdigest()

    def same_ot(pts_a, pts_b, i):
        ps_a = PointSet(n, pts_a)
        ps_b = PointSet(n, pts_b)
        for a in range(n):
            for b in range(a + 1, n):
                if a == i or b == i:
                    continue
                if ps_a.orientation(a, b, i) != ps_b.orientation(a, b, i):
                    return False
        return True

    seen = set()

    class Frame:
        __slots__ = ("pts", "count", "todo", "cur_i", "dirs")
        def __init__(self, pts, count):
            self.pts = pts
            self.count = count
            todo = list(range(n))
            random.shuffle(todo)
            self.todo = todo
            self.cur_i = None
            self.dirs = []

    key0 = ot_key(pts)
    seen.add(key0)
    stack = collections.deque([Frame(pts, start_count)])
    _steps = 0

    while stack:
        if max_steps and _steps >= max_steps:
            break
        _steps += 1
        frame = stack[-1]

        while not frame.dirs:
            if not frame.todo:
                stack.pop()
                break
            frame.cur_i = frame.todo.pop()
            frame.dirs = list(directions)
            random.shuffle(frame.dirs)

        if not stack:
            break
        frame = stack[-1]
        if not frame.dirs:
            continue

        i = frame.cur_i
        dx, dy = frame.dirs.pop()
        pts0 = list(frame.pts)
        x0, y0 = pts0[i]

        pts_tmp = list(pts0)
        step = 1
        x1, y1 = x0, y0
        grow = True
        diam = max(abs(x) for x, y in pts0) + max(abs(y) for x, y in pts0) + 1

        while step > 0:
            pts_tmp[i] = (x1 + step * dx, y1 + step * dy)
            if same_ot(pts0, pts_tmp, i):
                x1, y1 = pts_tmp[i]
                if grow:
                    step *= 2
            else:
                step //= 2
                grow = False
            if step > 100 * diam:
                break
        if step > 100 * diam:
            continue

        pts_new = list(pts0)
        for attempt in range(10):
            pts_new[i] = (x1 + (attempt + 1) * dx, y1 + (attempt + 1) * dy)
            if len(set(pts_new)) == n:
                ps = PointSet(n, pts_new)
                if not ps.has_collinear_points():
                    break
        else:
            continue

        new_sl = PointSet(n, pts_new).to_small_lambda()
        new_count = _count_property(new_sl, prop)

        accept = new_count <= frame.count
        if not accept and siman:
            temperature *= dT
            if frame.count > 0:
                prob = exp(-(new_count - frame.count) / (frame.count * temperature))
                accept = random.random() < prob

        if not accept:
            continue

        if new_count < min_count:
            min_count = new_count
            if verbose:
                print(f"  improved: {prop}={min_count}")
            yield new_sl
            if stop_if_improved:
                return

        key = ot_key(pts_new)
        if key in seen:
            continue
        seen.add(key)

        stack.append(Frame(_pts_normalize(pts_new), new_count))
        if len(stack) > trace:
            stack.popleft()


def _register_walk_points(sub) -> None:
    p = sub.add_parser(
        "walk-points",
        help="Local search in coordinate space to minimize a property",
        description=(
            "Search for order types with a smaller property value by moving\n"
            "points in coordinate space.  The OT changes at each step.\n"
            "Requires a concrete input format (b08/b16/asc/json).\n\n"
            "  default     DFS: moves each point in 16 rational directions via\n"
            "              binary search to the OT boundary, steps past it.\n"
            "              Each new OT neighbor is pushed onto the DFS stack.\n\n"
            "  --random    Random walk: pick a random point, move it by a random\n"
            "              offset; accept if property does not increase.\n\n"
            "Available properties:\n" + _PROP_HELP
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    add_input_args(p)
    p.add_argument("prop", help="Property to minimize (see above)")
    p.add_argument("--random", action="store_true", dest="random_walk",
                   help="Random walk mode instead of DFS")
    p.add_argument("--trials", type=int, default=0,
                   help="(--random) Max random steps; 0 = run forever (default: 0)")
    p.add_argument("--range", type=int, default=0, dest="walk_range",
                   help="(--random) Max displacement per step (default: 5 + diam/3)")
    p.add_argument("--trace", type=int, default=10000,
                   help="(DFS) Stack size limit (default: 10000)")
    p.add_argument("--max-steps", type=int, default=0,
                   help="(DFS) Max DFS steps; 0 = run forever (default: 0)")
    p.add_argument("--good-bits", type=int, default=30,
                   help="(DFS) Scale coords to this bit-width (default: 30)")
    p.add_argument("--stop-if-improved", action="store_true",
                   help="Stop after the first improvement")
    p.add_argument("--siman", action="store_true",
                   help="(DFS) Simulated annealing to accept worse neighbors")
    p.add_argument("--T0", type=float, default=0.1,
                   help="(DFS+siman) Initial temperature (default: 0.1)")
    p.add_argument("--dT", type=float, default=0.999,
                   help="(DFS+siman) Temperature decay per step (default: 0.999)")
    p.add_argument("-o", "--output", default=None,
                   help="Output file (default: input.walk.NNN.lt)")
    p.set_defaults(func=_cmd_walk_points)


def _cmd_walk_points(args) -> None:
    idx = 0
    for ot in open_input(args):
        for improved in walk_points(
            ot, args.prop,
            random_walk=args.random_walk,
            trials=args.trials,
            walk_range=args.walk_range,
            trace=args.trace,
            max_steps=args.max_steps,
            good_bits=args.good_bits,
            stop_if_improved=args.stop_if_improved,
            siman=args.siman,
            T0=args.T0,
            dT=args.dT,
        ):
            idx += 1
            out = args.output or _output_path(args.input, ".walk.lt", idx)
            write_order_types([improved], out, fmt="lt")
            print(f"written: {out}")


# ===========================================================================
# walk-abstract  — DFS (or random) on the flip graph (no coordinates)
# ===========================================================================

def walk_abstract(
    ot: SmallLambda,
    prop: str,
    *,
    random_walk: bool = False,
    trials: int = 0,
    trace: int = 10000,
    max_steps: int = 0,
    stop_if_improved: bool = False,
    siman: bool = False,
    T0: float = 0.1,
    dT: float = 0.999,
    verbose: bool = True,
) -> Iterator[SmallLambda]:
    """Local search on the flip graph of exit-edge triples to minimize a property.

    Two modes (selected via random_walk):

    DFS mode (random_walk=False):
        For each abstract OT on the stack: enumerate all exit-edge triples
        (a,b,c), flip each one, evaluate the property, push improving
        (or equal) neighbors onto the DFS stack.

    Random mode (random_walk=True):
        At each step: pick a random exit-edge triple and flip it; accept
        if the property does not increase.

    Works purely on abstract order types — no coordinates needed.
    Yields each strictly improving OT found (lex-min representative).
    """
    import collections
    import hashlib
    import random
    from math import exp
    from pyotlib2.algorithms.exit_edges import filter_exit_edges

    start_count = _count_property(ot, prop)
    min_count = start_count
    temperature = T0

    def ot_key(ot):
        return hashlib.md5(ot.to_string().encode()).hexdigest()

    if verbose:
        print(f"start: {prop}={start_count}")

    # ---- random walk mode ----
    if random_walk:
        cur_ot = ot
        cur_count = start_count
        _trial = 0
        while trials == 0 or _trial < trials:
            _trial += 1
            _, witnesses = filter_exit_edges(cur_ot, return_witnesses=True)
            triples = [(a, b, c) for (a, b), ws in witnesses.items() for c in ws]
            if not triples:
                break
            a, b, c = random.choice(triples)
            bl = cur_ot.to_big_lambda()
            new_bl = bl.flip_triple(a, b, c)
            try:
                new_sl = new_bl.to_small_lambda()
            except Exception:
                continue
            new_count = _count_property(new_sl, prop)
            if new_count > cur_count:
                continue
            if new_count < min_count:
                min_count = new_count
                lex = new_sl.get_lex_min()
                if verbose:
                    print(f"  improved: {prop}={min_count}")
                yield lex
                if stop_if_improved:
                    return
            cur_ot = new_sl
            cur_count = new_count
        return

    # ---- DFS mode ----
    seen = set()

    class Frame:
        __slots__ = ("ot", "count", "todo")
        def __init__(self, ot, count):
            self.ot = ot
            self.count = count
            _, witnesses = filter_exit_edges(ot, return_witnesses=True)
            todo = [(a, b, c) for (a, b), ws in witnesses.items() for c in ws]
            random.shuffle(todo)
            self.todo = todo

    key0 = ot_key(ot)
    seen.add(key0)
    stack = collections.deque([Frame(ot, start_count)])
    _steps = 0

    while stack:
        if max_steps and _steps >= max_steps:
            break
        _steps += 1
        frame = stack[-1]

        if not frame.todo:
            stack.pop()
            continue

        a, b, c = frame.todo.pop()
        bl = frame.ot.to_big_lambda()
        new_bl = bl.flip_triple(a, b, c)

        try:
            new_sl = new_bl.to_small_lambda()
        except Exception:
            continue

        new_count = _count_property(new_sl, prop)

        accept = new_count <= frame.count
        if not accept and siman:
            temperature *= dT
            if frame.count > 0:
                prob = exp(-(new_count - frame.count) / (frame.count * temperature))
                accept = random.random() < prob

        if not accept:
            continue

        if new_count < min_count:
            min_count = new_count
            lex = new_sl.get_lex_min()
            if verbose:
                print(f"  improved: {prop}={min_count}")
            yield lex
            if stop_if_improved:
                return

        key = ot_key(new_sl)
        if key in seen:
            continue
        seen.add(key)

        stack.append(Frame(new_sl, new_count))
        if len(stack) > trace:
            stack.popleft()


def _register_walk_abstract(sub) -> None:
    p = sub.add_parser(
        "walk-abstract",
        help="Local search on the flip graph to minimize a property (no coordinates)",
        description=(
            "Search for order types with a smaller property value by flipping\n"
            "exit-edge triples in the chirotope.  Works on abstract OTs —\n"
            "no coordinates needed (.lt/.blt input).\n\n"
            "  default     DFS on the flip graph: enumerate all exit-edge triples\n"
            "              and flip each to reach a neighboring OT.\n\n"
            "  --random    Random flip walk: at each step pick a random exit-edge\n"
            "              triple and flip it; accept if property does not increase.\n\n"
            "Available properties:\n" + _PROP_HELP
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    add_input_args(p)
    p.add_argument("prop", help="Property to minimize (see above)")
    p.add_argument("--random", action="store_true", dest="random_walk",
                   help="Random flip walk mode instead of DFS")
    p.add_argument("--trials", type=int, default=0,
                   help="(--random) Max random flips; 0 = run forever (default: 0)")
    p.add_argument("--trace", type=int, default=10000,
                   help="(DFS) Stack size limit (default: 10000)")
    p.add_argument("--max-steps", type=int, default=0,
                   help="(DFS) Max DFS steps; 0 = run forever (default: 0)")
    p.add_argument("--stop-if-improved", action="store_true",
                   help="Stop after the first improvement")
    p.add_argument("--siman", action="store_true",
                   help="(DFS) Simulated annealing to accept worse neighbors")
    p.add_argument("--T0", type=float, default=0.1,
                   help="(DFS+siman) Initial temperature (default: 0.1)")
    p.add_argument("--dT", type=float, default=0.999,
                   help="(DFS+siman) Temperature decay per step (default: 0.999)")
    p.add_argument("-o", "--output", default=None,
                   help="Output file (default: input.abswalk.NNN.lt)")
    p.set_defaults(func=_cmd_walk_abstract)


def _cmd_walk_abstract(args) -> None:
    idx = 0
    for ot in open_input(args):
        for improved in walk_abstract(
            ot, args.prop,
            random_walk=args.random_walk,
            trials=args.trials,
            trace=args.trace,
            max_steps=args.max_steps,
            stop_if_improved=args.stop_if_improved,
            siman=args.siman,
            T0=args.T0,
            dT=args.dT,
        ):
            idx += 1
            out = args.output or _output_path(args.input, ".abswalk.lt", idx)
            write_order_types([improved], out, fmt="lt")
            print(f"written: {out}")


# ===========================================================================
# extend-abstract  — enumerate all n+1 extensions
# ===========================================================================

def extend_abstract(
    ot: SmallLambda,
    *,
    unify_pcs: bool = False,
    method: str = "recursive",
    auto_relabel: bool = True,
) -> Iterator[SmallLambda]:
    """Enumerate all abstract OTs on n+1 points extending ot.

    Parameters
    ----------
    ot : SmallLambda
        Input order type on n points.
    unify_pcs : bool
        If True, deduplicate at projective-class level.
    method : str
        ``"recursive"`` (default) — fast backtracking with signotope pruning,
        requires natural labeling (point 0 on convex hull, all others to the
        right).  Ported from supplemental-universal-sets (Scheucher 2020),
        see https://doi.org/10.7155/jgaa.00529.

        ``"sat"`` — enumerate via SAT solver (CaDiCaL/python-sat).
        Slower but does not require natural labeling.
        Requires:  pip install pyotlib2[sat]
    auto_relabel : bool
        Only relevant for ``method="recursive"``.  If True (default), apply
        natural labeling automatically before extending.  If False, the input
        must already be in natural labeling (point 0 on hull with all others
        to its right); an AssertionError is raised otherwise.
    """
    if method == "recursive":
        yield from _extend_abstract_recursive(ot, unify_pcs=unify_pcs, auto_relabel=auto_relabel)
    elif method == "sat":
        yield from _extend_abstract_sat(ot, unify_pcs=unify_pcs)
    else:
        raise ValueError(f"unknown method {method!r}, choose 'recursive' or 'sat'")


def _extend_abstract_recursive(
    ot: SmallLambda,
    *,
    unify_pcs: bool = False,
    auto_relabel: bool = True,
) -> Iterator[SmallLambda]:
    """Recursive backtracking extension — port of extend_order_type.cpp.

    Requires natural labeling: point 0 must be on the convex hull and
    o[0,j,k] == -1 for all 0 < j < k < n  (all other points are to the
    right of the ray 0→…).
    """
    import numpy as np
    from pyotlib2.core.big_lambda import BigLambda

    seen: set = set()

    hull_pts = ot.get_extremal_points()

    for h in hull_pts:
        # Apply natural labeling so that hull point h becomes point 0
        lab = ot.get_natural_labeling(h)
        if auto_relabel:
            ot_nat = ot.relabeled(lab)
        else:
            # Verify natural labeling already in place
            assert lab[0] == 0, (
                "Input is not in natural labeling (point 0 not on hull). "
                "Pass auto_relabel=True or relabel the input first."
            )
            ot_nat = ot

        n = ot_nat.n
        n1 = n + 1  # size after extension (new point index = n)
        o_base = ot_nat.to_big_lambda().o  # shape (n, n, n)

        # Verify natural labeling: o[0,j,k] == -1 for all 0<j<k<n
        for j in range(1, n):
            for k in range(j + 1, n):
                assert int(o_base[0, j, k]) == -1, (
                    f"Not in natural labeling: o[0,{j},{k}] = {o_base[0,j,k]}"
                )

        # o_ext: mutable n1×n1×n1 array, initialized from o_base, new entries = 0
        o_ext = np.zeros((n1, n1, n1), dtype=np.int8)
        o_ext[:n, :n, :n] = o_base

        def set_triple(i, j, d, val):
            o_ext[i, j, d] = o_ext[j, d, i] = o_ext[d, i, j] = val
            o_ext[i, d, j] = o_ext[d, j, i] = o_ext[j, i, d] = -val

        def check_signotope(i, j):
            """Check signotope axiom for the newly assigned triple (i,j,n).

            For every k != i,j: form sorted 4-tuple (a,b,c,d=n) where
            {a,b,c} = {i,j,k} sorted.  The sign sequence
            χ(a,b,c), χ(a,b,n), χ(a,c,n), χ(b,c,n)
            must have at most one sign change.
            """
            d = n  # new point index
            for k in range(n):
                if k == i or k == j:
                    continue
                if k < i:
                    a, b, c = k, i, j
                elif k < j:
                    a, b, c = i, k, j
                else:
                    a, b, c = i, j, k
                s_abc = int(o_ext[a, b, c])
                s_abd = int(o_ext[a, b, d])
                s_acd = int(o_ext[a, c, d])
                s_bcd = int(o_ext[b, c, d])
                changes = (
                    (s_abc * s_abd == -1)
                    + (s_abd * s_acd == -1)
                    + (s_acd * s_bcd == -1)
                )
                if changes > 1:
                    return False
            return True

        def recurse(i, j):
            # Try both orientations; if i==0 only try o=-1 (natural labeling fix)
            orientations = [-1] if i == 0 else [-1, +1]
            for o_val in orientations:
                set_triple(i, j, n, o_val)
                if not check_signotope(i, j):
                    continue
                # Advance to next pair
                if j == n - 1:
                    if i == n - 2:
                        # All pairs assigned — record this extension
                        new_sl = BigLambda(n1, o_ext.copy()).to_small_lambda()
                        # Natural labeling around new point n, then lex-min
                        lab2 = new_sl.get_natural_labeling(n)
                        if lab2[0] != n:
                            continue  # new point not on hull → skip
                        new_sl_rel = new_sl.relabeled(lab2)
                        new_ot = new_sl_rel.get_lex_min()
                        if unify_pcs:
                            from pyotlib2.algorithms.projective_class import ProjectiveClass
                            new_ot = ProjectiveClass(new_ot).representer
                        key = new_ot.to_string()
                        if key not in seen:
                            seen.add(key)
                            yield new_ot
                    else:
                        yield from recurse(i + 1, i + 2)
                else:
                    yield from recurse(i, j + 1)
            set_triple(i, j, n, 0)  # reset

        yield from recurse(0, 1)


def _extend_abstract_sat(
    ot: SmallLambda,
    *,
    unify_pcs: bool = False,
) -> Iterator[SmallLambda]:
    """SAT-based extension — port of old pyotlib ExtendAbstract.py."""
    try:
        from pysat.solvers import Cadical195 as Solver
    except ImportError:
        raise RuntimeError(
            "python-sat is required: install with  pip install python-sat\n"
            "or  pip install pyotlib2[sat]"
        )
    from itertools import combinations
    import numpy as np
    from pyotlib2.core.big_lambda import BigLambda

    n = ot.n + 1  # new size (new point appended at end)
    o_old = ot.to_big_lambda().o  # shape (ot.n, ot.n, ot.n)

    all_variables = list(combinations(range(n), 3))
    var_of = {t: i + 1 for i, t in enumerate(all_variables)}

    def var(a, b, c):
        return var_of[(a, b, c)]

    seen: set = set()

    for i0 in range(n):
        constraints = []

        for I3 in combinations(range(n), 3):
            if i0 in I3:
                continue
            I4 = tuple(sorted(I3 + (i0,)))
            I4_triples = list(combinations(I4, 3))
            for t1, t2, t3 in combinations(I4_triples, 3):
                for sgn in (+1, -1):
                    constraints.append([sgn * var(*t1), -sgn * var(*t2), sgn * var(*t3)])

        for a, b, c in combinations(range(n - 1), 3):
            a2 = a if a < i0 else a + 1
            b2 = b if b < i0 else b + 1
            c2 = c if c < i0 else c + 1
            constraints.append([int(o_old[a, b, c]) * var(a2, b2, c2)])

        for sol in _iter_sat(Solver, constraints):
            o_new = [[[0] * n for _ in range(n)] for _ in range(n)]
            for a, b, c in all_variables:
                oabc = +1 if sol[var(a, b, c) - 1] > 0 else -1
                o_new[a][b][c] = o_new[b][c][a] = o_new[c][a][b] = +oabc
                o_new[a][c][b] = o_new[b][a][c] = o_new[c][b][a] = -oabc

            o_arr = np.array(o_new, dtype=np.int8)
            new_sl = BigLambda(n, o_arr).to_small_lambda()
            new_ot = new_sl.get_lex_min()

            if unify_pcs:
                from pyotlib2.algorithms.projective_class import ProjectiveClass
                new_ot = ProjectiveClass(new_ot).representer

            key = new_ot.to_string()
            if key not in seen:
                seen.add(key)
                yield new_ot


def _iter_sat(Solver, constraints):
    """Iterate all SAT solutions, blocking each after yielding."""
    n_vars = max(abs(lit) for clause in constraints for lit in clause)
    with Solver(bootstrap_with=constraints) as solver:
        while solver.solve():
            sol = solver.get_model()
            yield sol
            block = [-lit for lit in sol if 1 <= abs(lit) <= n_vars]
            solver.add_clause(block)


def _register_extend_abstract(sub) -> None:
    p = sub.add_parser(
        "extend-abstract",
        help="Enumerate all n+1 abstract OT extensions",
        description=(
            "For each input OT of n points, enumerate all abstract order types "
            "on n+1 points whose restriction to the original n points equals the "
            "input.  Outputs lex-min representatives.\n\n"
            "method=recursive (default): fast backtracking with signotope pruning "
            "(Scheucher 2020, https://doi.org/10.7155/jgaa.00529).\n"
            "method=sat: SAT solver (CaDiCaL); requires pip install pyotlib2[sat]"
        ),
    )
    add_input_args(p)
    add_output_args(p, ".ext")
    p.add_argument("--unify-pcs", action="store_true",
                   help="Deduplicate at projective-class level (slower)")
    p.add_argument("--method", choices=["recursive", "sat"], default="recursive",
                   help="Extension method (default: recursive)")
    p.add_argument("--no-auto-relabel", action="store_true",
                   help="Do not auto-apply natural labeling (recursive method only)")


def _cmd_extend_abstract(args) -> None:
    out, fmt = resolve_output(args, ".ext.lt")
    results = []
    for ot in open_input(args):
        n_before = len(results)
        for new_ot in extend_abstract(
            ot,
            unify_pcs=args.unify_pcs,
            method=args.method,
            auto_relabel=not args.no_auto_relabel,
        ):
            results.append(new_ot)
        print(f"  n={ot.n} → {len(results) - n_before} extensions")
    write_order_types(results, out, fmt="lt")
    print(f"total: {len(results)}  written to: {out}")


# ===========================================================================
# extend-random  — random point placement for n+1 extensions
# ===========================================================================

def extend_random(
    ot: SmallLambda,
    *,
    trials: int = 1000,
    expand: float = 1.0,
) -> Iterator[SmallLambda]:
    """Extend a realized OT by randomly placing an additional point.

    Tries up to `trials` random placements in a box expanded by `expand`
    times the diameter around the existing point set.  Each valid,
    non-collinear placement defines a new OT; duplicates are suppressed.

    Requires ot.realization to be set.
    Yields lex-min SmallLambda for each distinct extension found.
    """
    import random
    from pyotlib2.core.point_set import PointSet

    pts = _require_realization(ot, "extend-random")
    n = ot.n

    xs = [x for x, y in pts]
    ys = [y for x, y in pts]
    xlo, xhi = min(xs), max(xs)
    ylo, yhi = min(ys), max(ys)
    dx = max(xhi - xlo, 1) * expand
    dy = max(yhi - ylo, 1) * expand

    seen: set = set()

    for _ in range(trials):
        x = int(random.uniform(xlo - dx, xhi + dx))
        y = int(random.uniform(ylo - dy, yhi + dy))
        new_pts = pts + [(x, y)]

        ps = PointSet(n + 1, new_pts)
        if ps.has_collinear_points():
            continue

        new_sl = ps.to_small_lambda().get_lex_min()
        key = new_sl.to_string()
        if key in seen:
            continue
        seen.add(key)
        yield new_sl


def _register_extend_random(sub) -> None:
    p = sub.add_parser(
        "extend-random",
        help="Extend realized OTs by randomly placing one additional point",
        description=(
            "For each input OT (with concrete coordinates), try placing an "
            "extra point at random positions in an expanded bounding box.  "
            "Each non-collinear placement defines an n+1-point OT; distinct "
            "ones are output as lex-min representatives.  "
            "Requires a concrete input format (b08/b16/asc/json)."
        ),
    )
    add_input_args(p)
    add_output_args(p, ".ext")
    p.add_argument("--trials", type=int, default=1000,
                   help="Number of random placements to try (default: 1000)")
    p.add_argument("--expand", type=float, default=1.0,
                   help="Expand bounding box by this factor (default: 1.0)")
    p.set_defaults(func=_cmd_extend_random)


def _cmd_extend_random(args) -> None:
    out, fmt = resolve_output(args, ".ext.lt")
    results = []
    for ot in open_input(args):
        n_before = len(results)
        for new_ot in extend_random(ot, trials=args.trials, expand=args.expand):
            results.append(new_ot)
        print(f"  n={ot.n} → {len(results) - n_before} extensions found")
    write_order_types(results, out, fmt="lt")
    print(f"total: {len(results)}  written to: {out}")
