"""Exit-edge detection for order types.

An edge (a, b) is an *exit edge* iff there exists a point c such that
triangle (a, b, c) is empty and oriented consistently — meaning the edge
(a, b) "exits" the convex hull of some sub-configuration.  Exit edges
carry exactly the orientation constraints that are necessary for the
order type: flipping any non-exit edge preserves the OT.

The fast algorithm uses the rotation system: for each ordered pair (a, b),
scan one step clockwise and counter-clockwise to find the candidate
witness c, and verify the orientation matches.

Reference: old pyotlib FilterExitEdges.filter_exit_edges_fast
"""

from __future__ import annotations
from itertools import combinations
from typing import Optional

from pyotlib2.core.small_lambda import SmallLambda


def filter_exit_edges(
    ot: SmallLambda,
    return_witnesses: bool = False,
) -> "set | tuple[set, dict]":
    """Return the set of exit edges of an order type.

    Parameters
    ----------
    ot:
        The order type.
    return_witnesses:
        If True, also return a dict mapping each exit edge (a, b) to the
        set of witness points c (at most 2 per edge).

    Returns
    -------
    edges:
        Set of pairs (a, b) with a < b that are exit edges.
    witnesses (optional):
        Dict {(a, b): set of c} for each exit edge.
    """
    bl = ot.to_big_lambda()
    n = bl.n
    o = bl.o
    # unsigned rotation system: SRS[a] = list of other points sorted by
    # angle around a (CCW from the "rightmost" neighbour)
    SRS = bl.get_rotation_system(signed=False)

    edges: set = set()
    witnesses: dict = {}

    for a, b in combinations(range(n), 2):
        idx_a = SRS[a].index(b)
        idx_b = SRS[b].index(a)
        for sign in (-1, +1):
            a_next = (idx_a + sign) % (n - 1)
            b_next = (idx_b - sign) % (n - 1)
            c = SRS[a][a_next]
            if c == SRS[b][b_next] and int(o[a, b, c]) == sign:
                e = (a, b)
                edges.add(e)
                if return_witnesses:
                    witnesses.setdefault(e, set()).add(c)

    if return_witnesses:
        return edges, witnesses
    return edges


def exit_triples(ot: SmallLambda) -> list:
    """Return list of (a, b, c) orientation constraints from exit edges.

    Each triple satisfies: (a, b) is an exit edge, c is a witness.
    These are the minimal set of orientation constraints that fully
    determine the order type.
    """
    edges, witnesses = filter_exit_edges(ot, return_witnesses=True)
    triples = []
    for (a, b), ws in witnesses.items():
        for c in ws:
            triples.append((a, b, c))
    return triples
