"""Crossing family analysis.

A k-crossing-family is a set of k pairwise crossing edges.
"""

from __future__ import annotations
from itertools import combinations
from typing import Iterator

from pyotlib2.core.big_lambda import BigLambda
from pyotlib2.core.small_lambda import SmallLambda


def crossing_pairs(bl: BigLambda) -> list:
    """Return list of pairs of crossing edges ((a,b),(c,d))."""
    n = bl.n
    edges = list(combinations(range(n), 2))
    return [
        (e, f)
        for e, f in combinations(edges, 2)
        if bl.edges_cross(e, f)
    ]


def count_crossings_bl(bl: BigLambda) -> int:
    return len(crossing_pairs(bl))


def enumerate_crossing_families(
    bl: BigLambda, k: int
) -> Iterator[tuple]:
    """Yield k-tuples of pairwise-crossing edges."""
    pairs = crossing_pairs(bl)
    # Build adjacency: edge → set of edges it crosses
    n_edges = len(list(combinations(range(bl.n), 2)))
    edges = list(combinations(range(bl.n), 2))
    idx = {e: i for i, e in enumerate(edges)}

    adj: dict = {e: set() for e in edges}
    for e, f in pairs:
        adj[e].add(f)
        adj[f].add(e)

    def _clique(current: list, candidates: list) -> Iterator[tuple]:
        if len(current) == k:
            yield tuple(current)
            return
        for i, e in enumerate(candidates):
            new_cands = [f for f in candidates[i + 1:] if f in adj[e]]
            yield from _clique(current + [e], new_cands)

    # Prune: only consider edges with at least k-1 neighbours
    cands = [e for e in edges if len(adj[e]) >= k - 1]
    yield from _clique([], cands)


def count_crossing_families(bl: BigLambda, k: int) -> int:
    return sum(1 for _ in enumerate_crossing_families(bl, k))


def max_crossing_family_size(bl: BigLambda) -> int:
    """Return the size of the largest crossing family."""
    edges = list(combinations(range(bl.n), 2))
    adj = {e: set() for e in edges}
    for e, f in crossing_pairs(bl):
        adj[e].add(f)
        adj[f].add(e)

    # Try sizes from large to small
    for k in range(len(edges), 0, -1):
        if any(enumerate_crossing_families(bl, k)):
            return k
    return 0
