"""Crossing family analysis.

A k-crossing-family is a set of k pairwise crossing edges (segments between
point pairs of the complete straight-line graph).  Equivalently, it is a
k-clique in the *crossing graph* whose vertices are the C(n,2) edges of the
point set and whose edges connect pairs that properly cross.

Algorithms
----------
``pruned``  (default)
    Two-phase degree-pruning before a plain backtracking k-clique search.

    Phase 1 — degree pruning: iteratively remove any vertex whose degree in
    the crossing graph is < k-1.  A vertex with too few neighbours can never
    be part of a k-clique.

    Phase 2 — geometric (``realDeg``) pruning: for each segment edge (a,b),
    classify its crossing neighbours into "left" (c lands left of a→b) and
    "right" groups.  A k-crossing-family containing (a,b) needs at least k-1
    further edges that all cross (a,b); each such edge contributes one point
    to each side, so min(|left|, |right|) ≥ k-1 is necessary.  Iteratively
    remove edges that fail this condition.

    After pruning, a backtracking clique enumerator (with the standard
    ``candidates[i+1:]`` restriction) collects exactly the k-cliques.

    This mirrors the ``count_k_families_fast`` implementation from pyotlib 1.
"""

from __future__ import annotations
from itertools import combinations
from typing import Iterator

from pyotlib2.core.big_lambda import BigLambda


# ---------------------------------------------------------------------------
# Building the crossing graph
# ---------------------------------------------------------------------------

def _build_adj(bl: BigLambda) -> tuple[list, dict]:
    """Return (edges, adj) for the crossing graph of *bl*."""
    edges = list(combinations(range(bl.n), 2))
    adj: dict[tuple, set] = {e: set() for e in edges}
    for e, f in combinations(edges, 2):
        if bl.edges_cross(e, f):
            adj[e].add(f)
            adj[f].add(e)
    return edges, adj


# ---------------------------------------------------------------------------
# Pruning helpers
# ---------------------------------------------------------------------------

def _prune_degree(adj: dict, k: int) -> dict:
    """Iteratively remove vertices with degree < k-1 (modifies a copy)."""
    adj = {v: set(nbrs) for v, nbrs in adj.items()}
    changed = True
    while changed:
        changed = False
        to_remove = [v for v, nbrs in adj.items() if len(nbrs) < k - 1]
        for v in to_remove:
            for u in adj.pop(v):
                adj[u].discard(v)
            changed = True
    return adj


def _real_deg(bl: BigLambda, adj: dict) -> dict[tuple, int]:
    """Geometric degree: for edge (a,b), count min(left-nbrs, right-nbrs).

    For a crossing edge (c,d): one of c,d lies left of a→b and one right.
    Assign the left-side point to *left*, the right-side point to *right*.
    A k-crossing family containing (a,b) needs k-1 further edges each
    contributing one point per side, so min(|left|,|right|) >= k-1.
    """
    real: dict[tuple, int] = {}
    for v, nbrs in adj.items():
        a, b = v
        left: set = set()
        right: set = set()
        for w in nbrs:
            c, d = w
            # ensure c is the point on the left side of a→b
            if bl.o[a][b][c] != 1:
                c, d = d, c
            left.add(c)
            right.add(d)
        real[v] = min(len(left), len(right))
    return real


def _prune_geometric(bl: BigLambda, adj: dict, k: int) -> dict:
    """Iteratively remove edges whose geometric degree < k-1."""
    adj = {v: set(nbrs) for v, nbrs in adj.items()}
    changed = True
    while changed:
        changed = False
        real = _real_deg(bl, adj)
        to_remove = [v for v, d in real.items() if d < k - 1]
        for v in to_remove:
            for u in adj.pop(v):
                adj[u].discard(v)
            changed = True
    return adj


# ---------------------------------------------------------------------------
# Backtracking k-clique enumerator
# ---------------------------------------------------------------------------

def _enum_cliques(adj: dict, k: int) -> Iterator[tuple]:
    """Yield k-cliques from the subgraph defined by *adj* (dict v→set)."""
    vertices = sorted(adj)
    order = {v: i for i, v in enumerate(vertices)}

    def _bt(current: list, cands: list) -> Iterator[tuple]:
        if len(current) == k:
            yield tuple(current)
            return
        for i, v in enumerate(cands):
            new_cands = [u for u in cands[i + 1:] if u in adj[v]]
            yield from _bt(current + [v], new_cands)

    yield from _bt([], vertices)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def crossing_pairs(bl: BigLambda) -> list:
    """Return list of pairs of crossing edges ``((a,b),(c,d))``."""
    edges = list(combinations(range(bl.n), 2))
    return [
        (e, f)
        for e, f in combinations(edges, 2)
        if bl.edges_cross(e, f)
    ]


def count_crossings_bl(bl: BigLambda) -> int:
    """Number of crossing edge pairs (= rectilinear crossing number)."""
    return len(crossing_pairs(bl))


def enumerate_crossing_families(
    bl: BigLambda,
    k: int,
    *,
    algo: str = "pruned",
) -> Iterator[tuple]:
    """Yield all k-tuples of pairwise-crossing edges.

    Parameters
    ----------
    bl:   BigLambda of the order type.
    k:    desired crossing-family size.
    algo: ``"pruned"`` (default) — two-phase degree+geometric pruning before
          backtracking.  ``"basic"`` — plain backtracking with only the cheap
          degree-1 pre-filter (faster for very small k or sparse graphs).
    """
    _, adj = _build_adj(bl)

    if algo == "basic":
        # Cheap degree filter only
        cands = {v: nbrs for v, nbrs in adj.items() if len(nbrs) >= k - 1}
        yield from _enum_cliques(cands, k)

    elif algo == "pruned":
        # Phase 1: degree pruning
        adj = _prune_degree(adj, k)
        if not adj:
            return
        # Phase 2: geometric pruning
        adj = _prune_geometric(bl, adj, k)
        if not adj:
            return
        yield from _enum_cliques(adj, k)

    else:
        raise ValueError(f"unknown algo {algo!r}; choose 'pruned' or 'basic'")


def count_crossing_families(
    bl: BigLambda,
    k: int,
    *,
    algo: str = "pruned",
) -> int:
    """Count k-crossing families (k-cliques in the crossing graph)."""
    return sum(1 for _ in enumerate_crossing_families(bl, k, algo=algo))


def max_crossing_family_size(bl: BigLambda, *, algo: str = "pruned") -> int:
    """Return the size of the largest crossing family."""
    _, adj = _build_adj(bl)
    max_possible = len(adj)
    for k in range(max_possible, 0, -1):
        if any(enumerate_crossing_families(bl, k, algo=algo)):
            return k
    return 0
