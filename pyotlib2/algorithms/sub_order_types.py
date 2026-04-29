"""Sub-order-type enumeration and counting."""

from __future__ import annotations
from itertools import combinations
from typing import Iterable, Iterator

from pyotlib2.core.small_lambda import SmallLambda
from pyotlib2.algorithms.unify import unify


def enumerate_sub_ots(
    ot: SmallLambda,
    k: int,
    lex_min: bool = True,
) -> Iterator[SmallLambda]:
    """Yield all k-point sub-order-types of ot."""
    yield from ot.reduce(k, lex_min=lex_min)


def count_distinct_sub_ots(ot: SmallLambda, k: int) -> int:
    """Return number of distinct k-point sub-order-types."""
    return sum(1 for _ in unify(enumerate_sub_ots(ot, k)))


def find_sub_ots(
    ots: Iterable[SmallLambda],
    references: list,
    k: int,
) -> Iterator[tuple]:
    """For each ot in ots, yield (ot, matched_refs) where matched_refs are
    reference indices whose OT appears as a k-sub-order-type of ot."""
    ref_keys = {r.get_lex_min().to_string(): i for i, r in enumerate(references)}
    for ot in ots:
        matched = set()
        for sub in enumerate_sub_ots(ot, k):
            key = sub.to_string()
            if key in ref_keys:
                matched.add(ref_keys[key])
        yield ot, sorted(matched)
