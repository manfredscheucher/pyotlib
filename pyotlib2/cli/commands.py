"""CLI command implementations for pyotlib2.

Each command is also importable as a regular Python function for use in
IPython / Jupyter notebooks.
"""

from __future__ import annotations
import sys
from typing import Iterable, Iterator, Optional

from pyotlib2.core.small_lambda import SmallLambda
from pyotlib2.io.readers import read_order_types
from pyotlib2.io.writers import write_order_types
from pyotlib2.cli.io_args import (
    add_input_args, add_output_args, open_input, resolve_output, progress_iter
)


# ---------------------------------------------------------------------------
# Registration helper
# ---------------------------------------------------------------------------

def register_all(sub) -> None:
    _register_unify_ot(sub)
    _register_polygon_count(sub)
    _register_count_sub_ots(sub)
    _register_find_sub_ots(sub)
    _register_relabel_ot(sub)
    _register_sort_ots(sub)
    _register_shuffle_ots(sub)
    _register_realize(sub)
    _register_property_count(sub)


# ---------------------------------------------------------------------------
# unifyOT
# ---------------------------------------------------------------------------

def unify_ot(
    ots: Iterable[SmallLambda],
    calc_lex_min: bool = True,
    validate: bool = True,
) -> Iterator[SmallLambda]:
    """Remove duplicate order types.

    Can be used directly in Python::

        from pyotlib2 import read_order_types
        from pyotlib2.cli.commands import unify_ot
        unique = list(unify_ot(read_order_types("otypes06.b08", n=6)))
    """
    from pyotlib2.algorithms.unify import unify
    yield from unify(ots, calc_lex_min=calc_lex_min, validate=validate)


def _register_unify_ot(sub) -> None:
    p = sub.add_parser("unifyOT", help="Remove duplicate order types")
    add_input_args(p)
    add_output_args(p, ".OT")
    p.add_argument("--no-lexmin", action="store_false", dest="calc_lex_min",
                   help="Skip lex-min normalization")
    p.add_argument("--no-validate", action="store_false", dest="validate",
                   help="Skip collinearity check")
    p.set_defaults(func=_cmd_unify_ot, calc_lex_min=True, validate=True)


def _cmd_unify_ot(args) -> None:
    ots = progress_iter(open_input(args), "reading")
    unique = list(unify_ot(ots, calc_lex_min=args.calc_lex_min, validate=args.validate))
    out, fmt = resolve_output(args, ".OT.lt")
    cnt = write_order_types(unique, out, fmt=fmt)
    print(f"Input: {sum(1 for _ in open_input(args))}  Unique: {cnt}")


# ---------------------------------------------------------------------------
# polygonCount
# ---------------------------------------------------------------------------

def polygon_count(
    ots: Iterable[SmallLambda],
    k: int,
    empty_only: bool = True,
) -> Iterator[tuple]:
    """Yield (ot, count) for empty/convex k-gon counts.

    Example::

        from pyotlib2.cli.commands import polygon_count
        for ot, cnt in polygon_count(read_order_types("otypes06.b08", n=6), k=5):
            print(cnt)
    """
    from pyotlib2.algorithms.polygon_count import count_polygons

    for ot in ots:
        bl = ot.to_big_lambda()
        cnt = count_polygons(bl, k, empty_only=empty_only)
        yield ot, cnt


def _register_polygon_count(sub) -> None:
    p = sub.add_parser("polygonCount", help="Count empty/convex k-gons")
    add_input_args(p)
    p.add_argument("-k", type=int, required=True, help="Polygon size")
    p.add_argument("--convex", action="store_false", dest="empty_only",
                   help="Count all convex k-gons (not only empty ones)")
    p.add_argument("--enumerate", action="store_true", dest="enumerate",
                   help="Print each polygon found")
    p.set_defaults(func=_cmd_polygon_count, empty_only=True, enumerate=False)


def _cmd_polygon_count(args) -> None:
    from pyotlib2.algorithms.polygon_count import enumerate_polygons, count_polygons

    for ot in progress_iter(open_input(args), "polygonCount"):
        bl = ot.to_big_lambda()
        if args.enumerate:
            for poly in enumerate_polygons(bl, args.k, empty_only=args.empty_only):
                print(poly)
        else:
            cnt = count_polygons(bl, args.k, empty_only=args.empty_only)
            print(cnt)


# ---------------------------------------------------------------------------
# countSubOTs
# ---------------------------------------------------------------------------

def count_sub_ots(
    ots: Iterable[SmallLambda],
    k: int,
) -> Iterator[tuple]:
    """Yield (ot, count) of distinct k-point sub-order-types."""
    from pyotlib2.algorithms.sub_order_types import count_distinct_sub_ots

    for ot in ots:
        yield ot, count_distinct_sub_ots(ot, k)


def _register_count_sub_ots(sub) -> None:
    p = sub.add_parser("countSubOTs", help="Count distinct k-point sub-order-types")
    add_input_args(p)
    p.add_argument("-k", type=int, required=True, help="Sub-order-type size")
    p.set_defaults(func=_cmd_count_sub_ots)


def _cmd_count_sub_ots(args) -> None:
    max_cnt = 0
    for ot, cnt in progress_iter(count_sub_ots(open_input(args), args.k), "countSubOTs"):
        max_cnt = max(max_cnt, cnt)
        print(cnt)
    print(f"max: {max_cnt}", file=sys.stderr)


# ---------------------------------------------------------------------------
# findSubOTs
# ---------------------------------------------------------------------------

def find_sub_ots(
    ots: Iterable[SmallLambda],
    references: Iterable[SmallLambda],
    k: int,
) -> Iterator[tuple]:
    """Yield (ot, matched_ref_indices) for OTs containing reference sub-OTs."""
    from pyotlib2.algorithms.sub_order_types import find_sub_ots as _find
    refs = list(references)
    yield from _find(ots, refs, k)


def _register_find_sub_ots(sub) -> None:
    p = sub.add_parser("findSubOTs", help="Find OTs containing specific sub-OTs")
    add_input_args(p)
    p.add_argument("--ref", required=True, dest="ref", help="Reference OT file")
    p.add_argument("--ref-fmt", default=None, dest="ref_fmt")
    p.add_argument("--ref-n", type=int, default=None, dest="ref_n")
    p.add_argument("-k", type=int, required=True)
    p.set_defaults(func=_cmd_find_sub_ots)


def _cmd_find_sub_ots(args) -> None:
    refs = list(read_order_types(args.ref, fmt=args.ref_fmt, n=args.ref_n))
    for ot, matched in find_sub_ots(open_input(args), refs, args.k):
        print(ot.to_string().strip(), "->", matched)


# ---------------------------------------------------------------------------
# relabelOT
# ---------------------------------------------------------------------------

def relabel_ot(
    ots: Iterable[SmallLambda],
    calc_lex_min: bool = True,
) -> Iterator[SmallLambda]:
    """Relabel order types to their lex-min representative."""
    for ot in ots:
        yield ot.get_lex_min() if calc_lex_min else ot


def _register_relabel_ot(sub) -> None:
    p = sub.add_parser("relabelOT", help="Relabel OTs to lex-min representative")
    add_input_args(p)
    add_output_args(p, ".rel")
    p.set_defaults(func=_cmd_relabel_ot)


def _cmd_relabel_ot(args) -> None:
    ots = relabel_ot(open_input(args))
    out, fmt = resolve_output(args, ".rel.lt")
    cnt = write_order_types(ots, out, fmt=fmt)
    print(f"Written: {cnt}")


# ---------------------------------------------------------------------------
# sortOTs
# ---------------------------------------------------------------------------

def sort_ots(ots: Iterable[SmallLambda]) -> list:
    """Return order types sorted lexicographically."""
    return sorted(ots)


def _register_sort_ots(sub) -> None:
    p = sub.add_parser("sortOTs", help="Sort order types lexicographically")
    add_input_args(p)
    add_output_args(p, ".sorted")
    p.set_defaults(func=_cmd_sort_ots)


def _cmd_sort_ots(args) -> None:
    ots = sort_ots(open_input(args))
    out, fmt = resolve_output(args, ".sorted.lt")
    cnt = write_order_types(ots, out, fmt=fmt)
    print(f"Written: {cnt}")


# ---------------------------------------------------------------------------
# shuffleOTs
# ---------------------------------------------------------------------------

def shuffle_ots(ots: Iterable[SmallLambda]) -> list:
    """Return order types in random order."""
    import random
    lst = list(ots)
    random.shuffle(lst)
    return lst


def _register_shuffle_ots(sub) -> None:
    p = sub.add_parser("shuffleOTs", help="Shuffle order types randomly")
    add_input_args(p)
    add_output_args(p, ".shuffled")
    p.set_defaults(func=_cmd_shuffle_ots)


def _cmd_shuffle_ots(args) -> None:
    ots = shuffle_ots(open_input(args))
    out, fmt = resolve_output(args, ".shuffled.lt")
    cnt = write_order_types(ots, out, fmt=fmt)
    print(f"Written: {cnt}")


# ---------------------------------------------------------------------------
# realize
# ---------------------------------------------------------------------------

def realize(
    ots: Iterable[SmallLambda],
    method: str = "scipy",
    trials: int = 20,
) -> Iterator[tuple]:
    """Test realizability of abstract order types.

    Yields (ot, result) where result is True/False/None (unknown).

    Parameters
    ----------
    method:
        ``"gp"`` for GLPK Grassmann-Plucker LP,
        ``"scipy"`` for nonlinear optimization.
    """
    if method == "gp":
        from pyotlib2.realization.gp_tester import GPRealizationTester
        tester = GPRealizationTester()
    elif method == "scipy":
        from pyotlib2.realization.scipy_tester import ScipyRealizationTester
        tester = ScipyRealizationTester(trials=trials)
    else:
        raise ValueError(f"Unknown method: {method!r}")

    for ot in ots:
        yield ot, tester.is_realizable(ot)


def _register_realize(sub) -> None:
    p = sub.add_parser("realize", help="Test realizability of order types")
    add_input_args(p)
    p.add_argument("--method", default="scipy", choices=["scipy", "gp"],
                   help="Realization method (default: scipy)")
    p.add_argument("--trials", type=int, default=20,
                   help="Number of optimization trials (scipy only)")
    p.set_defaults(func=_cmd_realize)


def _cmd_realize(args) -> None:
    results = {True: 0, False: 0, None: 0}
    for ot, res in realize(open_input(args), method=args.method, trials=args.trials):
        results[res] += 1
        tag = "REAL" if res else ("NONR" if res is False else "IDK")
        print(f"{tag}: {ot.to_string().strip()}")
    print(f"\nRealizable: {results[True]}  Non-realizable: {results[False]}  Unknown: {results[None]}")


# ---------------------------------------------------------------------------
# propertyCount
# ---------------------------------------------------------------------------

def property_count(
    ots: Iterable[SmallLambda],
    properties: list,
) -> Iterator[tuple]:
    """Yield (ot, {prop: value, ...}) for each OT.

    Supported properties: ``cr`` (crossings), ``c3h``..``c9h`` (empty k-gons),
    ``c3g``..``c9g`` (convex k-gons), ``cf2``..``cf9`` (crossing families),
    ``extr`` (extremal points), ``onion_layers`` (number of convex layers).
    """
    from pyotlib2.algorithms.polygon_count import count_polygons, count_crossings
    from pyotlib2.algorithms.crossings import count_crossing_families

    for ot in ots:
        bl = ot.to_big_lambda()
        values = {}
        for prop in properties:
            if prop == "cr":
                values[prop] = count_crossings(ot)
            elif prop.startswith("c") and prop.endswith("h"):
                k = int(prop[1:-1])
                values[prop] = count_polygons(bl, k, empty_only=True)
            elif prop.startswith("c") and prop.endswith("g"):
                k = int(prop[1:-1])
                values[prop] = count_polygons(bl, k, empty_only=False)
            elif prop.startswith("cf"):
                k = int(prop[2:])
                values[prop] = count_crossing_families(bl, k)
            elif prop == "extr":
                values[prop] = len(ot.get_extremal_points())
            elif prop == "onion_layers":
                values[prop] = len(bl.get_onion())
            else:
                values[prop] = None
        yield ot, values


def _register_property_count(sub) -> None:
    p = sub.add_parser("propertyCount", help="Compute combinatorial properties")
    add_input_args(p)
    p.add_argument("--props", nargs="+", required=True, metavar="PROP",
                   help="Properties to compute: cr, c5h, c5g, cf3, extr, onion_layers, ...")
    p.set_defaults(func=_cmd_property_count)


def _cmd_property_count(args) -> None:
    for ot, values in progress_iter(
        property_count(open_input(args), args.props), "propertyCount"
    ):
        print(" ".join(str(values[p]) for p in args.props))
