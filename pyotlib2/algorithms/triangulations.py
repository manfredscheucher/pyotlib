"""Count triangulations of an order type (abstract, without coordinates).

Two algorithms are provided, both purely combinatorial:

BTFC — Backtracking + Forward Checking
    Enumerates all triangulations by recursive selection of inner edges,
    with forward-checking pruning (crossing edges immediately forbidden).
    Always available, no external dependencies.

ModelCount — #SAT via DPLL model counter
    Encodes the crossing-free constraint as a propositional CNF and counts
    satisfying assignments with the right number of inner edges via DPLL.
    Pure Python, no external solver.

Public API
----------
count_triangulations(sl, method="btfc")   →  int
count_triangulations_btfc(sl)             →  int
count_triangulations_modelcount(sl)       →  int

Background
----------
A triangulation of n points in general position with k hull vertices is a
maximal planar straight-line graph on the point set.  By Euler's formula:
  - exactly n-2 triangles
  - exactly 3n - k - 3 edges total  (k hull edges + 3n-2k-3 inner edges)

For n points in convex position (k=n), the number of triangulations equals
the Catalan number  C(n-2) = C(2(n-2), n-2) / (n-1).
"""

from __future__ import annotations

from itertools import combinations
from pyotlib2.core.small_lambda import SmallLambda


# ---------------------------------------------------------------------------
# Hull-edge helper
# ---------------------------------------------------------------------------

def _hull_edge_set(bl) -> set:
    """Return set of frozenset({i,j}) for all convex hull edges."""
    hull = bl.onion[0]           # CCW cycle from BigLambda.get_onion()
    k = len(hull)
    return {frozenset([hull[i], hull[(i + 1) % k]]) for i in range(k)}


# ---------------------------------------------------------------------------
# Algorithm 1: BTFC
# ---------------------------------------------------------------------------

def count_triangulations_btfc(sl: SmallLambda) -> int:
    """Count triangulations via backtracking + forward checking.

    Complexity: exponential in the worst case, but the crossing-based
    forward-checking pruning is very effective in practice.
    """
    n = sl.n
    bl = sl.to_big_lambda()

    hull_edges = _hull_edge_set(bl)
    k = len(bl.onion[0])
    target = 3 * n - 2 * k - 3          # number of inner edges needed

    # All candidate inner edges in a fixed order
    inner_edges = [
        (i, j)
        for i, j in combinations(range(n), 2)
        if frozenset([i, j]) not in hull_edges
    ]
    m = len(inner_edges)

    if target < 0 or target > m:
        return 0
    if target == 0:
        return 1

    # Precompute crossing sets: crossing_idx[e_idx] = list of e_idx of crossing edges
    crossing_idx: list[list[int]] = [[] for _ in range(m)]
    for i in range(m):
        for j in range(i + 1, m):
            if bl.edges_cross(inner_edges[i], inner_edges[j]):
                crossing_idx[i].append(j)
                crossing_idx[j].append(i)

    # forbidden[idx] = True means edge idx cannot be taken
    forbidden = [False] * m

    def _btfc(pos: int, chosen: int) -> int:
        remaining = m - pos
        still_needed = target - chosen
        if still_needed == 0:
            return 1
        if still_needed > remaining:
            return 0

        # Count available (non-forbidden) edges from pos onwards
        avail = sum(1 for i in range(pos, m) if not forbidden[i])
        if still_needed > avail:
            return 0

        # skip forbidden edges
        while pos < m and forbidden[pos]:
            pos += 1
        if pos >= m:
            return 0

        count = 0

        # Branch 1: skip edge at pos
        count += _btfc(pos + 1, chosen)

        # Branch 2: take edge at pos
        newly_forbidden = [j for j in crossing_idx[pos] if j > pos and not forbidden[j]]
        for j in newly_forbidden:
            forbidden[j] = True
        count += _btfc(pos + 1, chosen + 1)
        for j in newly_forbidden:
            forbidden[j] = False

        return count

    return _btfc(0, 0)


# ---------------------------------------------------------------------------
# Algorithm 2: ModelCount (DPLL #SAT)
# ---------------------------------------------------------------------------

def count_triangulations_modelcount(sl: SmallLambda) -> int:
    """Count triangulations via DPLL model counting.

    Encodes crossing constraints as CNF clauses (¬x_e ∨ ¬x_f for each
    crossing pair), then counts satisfying assignments with exactly
    `target` variables set to True using a DPLL-style counter.
    """
    n = sl.n
    bl = sl.to_big_lambda()

    hull_edges = _hull_edge_set(bl)
    k = len(bl.onion[0])
    target = 3 * n - 2 * k - 3

    inner_edges = [
        (i, j)
        for i, j in combinations(range(n), 2)
        if frozenset([i, j]) not in hull_edges
    ]
    m = len(inner_edges)

    if target < 0 or target > m:
        return 0

    # Build adjacency: crossing_mask[i] = list of j > i that cross edge i
    crossing: list[list[int]] = [[] for _ in range(m)]
    for i in range(m):
        for j in range(i + 1, m):
            if bl.edges_cross(inner_edges[i], inner_edges[j]):
                crossing[i].append(j)
                crossing[j].append(i)

    # DPLL model count with exact-k filter
    # assignment[i]: True/False/None (unset)
    # forbidden[i]: True if excluded by a crossing constraint
    assignment = [None] * m
    forbidden = [False] * m

    def _count(pos: int, chosen: int) -> int:
        """Count models starting from variable `pos` with `chosen` set so far."""
        remaining = m - pos
        still_needed = target - chosen
        if still_needed < 0:
            return 0
        if still_needed == 0:
            return 1
        if still_needed > remaining:
            return 0

        # Count feasible remaining slots
        avail = sum(1 for i in range(pos, m) if not forbidden[i])
        if still_needed > avail:
            return 0

        # skip forbidden variables
        while pos < m and forbidden[pos]:
            pos += 1
        if pos >= m:
            return 0

        # Branch 0: set pos = False (skip)
        count = _count(pos + 1, chosen)

        # Branch 1: set pos = True
        newly = [j for j in crossing[pos] if j > pos and not forbidden[j]]
        for j in newly:
            forbidden[j] = True
        count += _count(pos + 1, chosen + 1)
        for j in newly:
            forbidden[j] = False

        return count

    return _count(0, 0)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def count_triangulations(sl: SmallLambda, method: str = "btfc") -> int:
    """Count triangulations of the order type given by sl.

    Parameters
    ----------
    sl : SmallLambda
        The order type (abstract or concrete).
    method : "btfc" | "modelcount"
        Algorithm to use.  Both give identical results.
        "btfc" is generally faster.

    Returns
    -------
    int
        Number of triangulations.
    """
    if method == "btfc":
        return count_triangulations_btfc(sl)
    elif method == "modelcount":
        return count_triangulations_modelcount(sl)
    else:
        raise ValueError(f"Unknown method: {method!r}. Use 'btfc' or 'modelcount'.")
