"""Unification: reduce a list of order types to unique representatives."""

from __future__ import annotations
from typing import Iterable, Iterator

from pyotlib2.core.small_lambda import SmallLambda


def unify(
    ots: Iterable[SmallLambda],
    calc_lex_min: bool = True,
    validate: bool = True,
) -> Iterator[SmallLambda]:
    """Yield unique order types from ots.

    Parameters
    ----------
    ots:
        Input iterable of SmallLambda objects.
    calc_lex_min:
        If True, normalise each OT to its lexicographically minimal labeling
        before deduplication.
    validate:
        If True, skip OTs with collinear points.
    """
    seen: set = set()
    for ot in ots:
        if validate and not ot.is_valid():
            continue
        if calc_lex_min:
            ot = ot.get_lex_min()
        key = ot.to_string()
        if key not in seen:
            seen.add(key)
            yield ot
