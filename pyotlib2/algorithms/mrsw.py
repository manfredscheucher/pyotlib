"""Count empty convex k-gons (k-holes) via the MRSW algorithm.

Reference
---------
J.S.B. Mitchell, G. Rote, G. Sundaram, G. Woeginger:
"Counting Convex Polygons in Planar Point Sets"
Information Processing Letters 56 (1995) 45-49.
https://www.semanticscholar.org/paper/Counting-Convex-Polygons-in-Planar-Point-Sets-Mitchell-Rote/0782a8fa7a0d569c16b50a7596a6646caf2ea767

Algorithm (Section 4 of the paper)
------------------------------------
Fix a lowest point s.  U_s = all other points with larger y-coordinate,
sorted in CW angular order around s.

Define G(p, q, j; s) = number of empty convex j-gons with lowest vertex s,
  edges qp and ps (p adjacent to s, q before p in the chain).

Recursion:
  G(p, q, j; s) = 0                    if △pqs contains a point of S
               = 1                    if △pqs is empty and j = 3
               = Σ G(q, r, j-1; s)   otherwise,
  where r ∈ U_s ∩ H_{p,q} ∩ H_{s,q}  (H_{a,b} = left half-plane of a→b).

Total count of k-gons:
  Σ_s  Σ_{p ∈ U_s}  Σ_{q ∈ U_s ∩ H_{s,p}}  G(p, q, k-1; s)

Each k-gon is counted exactly once: at its lowest vertex s.

Abstract implementation
-----------------------
1. Apply natural labeling once (around any hull point) → points 0..n-1
   in CW angular order.  In this labeling, higher index = "later" in the
   CW sweep = geometrically "to the right / above".

2. Iterate s = n-1, n-2, …, 0 (highest index first as anchor).
   For each s, count k-holes where s is the HIGHEST-indexed vertex, i.e.
   U_s = {0, 1, …, s-1} (all points with smaller index).
   This replaces "above s in y-coordinate" with "smaller CW index than s".
   Each k-hole is counted exactly once: at its highest-index vertex.

3. After counting for anchor s, "remove" s (shrink the point set).

In pyotlib2's natural labeling (CW sweep):
  o[a,b,c] = +1  means c is to the LEFT of a→b (CCW orientation).

Conditions for r ∈ U_s ∩ H_{p,q} ∩ H_{s,q}  (s = anchor, all in 0..s-1):
  - r ∈ H_{p,q}: o[p, q, r] == +1   (r left of p→q)
  - r ∈ H_{s,q}: o[s, q, r] == +1   (r left of s→q)
  - q ∈ H_{s,p}: o[s, p, q] == +1   (q left of s→p)

Public API
----------
count_empty_kgons_mrsw(sl, k)   →  int
count_all_kgons_mrsw(sl, k_max) →  dict {k: count}
"""

from __future__ import annotations

import numpy as np

from pyotlib2.core.small_lambda import SmallLambda


# ---------------------------------------------------------------------------
# Core: count empty k-gons for ONE anchor s, using points 0..s-1 as U_s
# ---------------------------------------------------------------------------

def _count_kholes_anchor_s(o: np.ndarray, s: int, k: int) -> int:
    """Count empty convex k-gons with anchor s and all other vertices in 0..s-1.

    o[a,b,c] = +1 means c is to the LEFT of a→b (CCW).

    Conditions (directly from the paper, translated to o-matrix):
      - q ∈ H_{s,p}: o[s, p, q] == +1
      - r ∈ H_{p,q}: o[p, q, r] == +1
      - r ∈ H_{s,q}: o[s, q, r] == +1
      - triangle (s, p, q) must be empty of points from 0..s-1 \ {p,q}
    """
    m = s  # points available: 0..s-1
    if m < k - 1:
        return 0

    pts = list(range(s))  # U_s = {0, 1, ..., s-1}

    # ------------------------------------------------------------------
    # Precompute empty-triangle table for pairs (p, q) in U_s.
    # empty[(p,q)] = True iff triangle (s, p, q) contains no point of U_s.
    # ------------------------------------------------------------------
    empty: dict[tuple[int, int], bool] = {}
    for p in pts:
        for q in pts:
            if p == q:
                continue
            # sides of the three edges of triangle (s, p, q)
            ssp_q = int(o[s, p, q])
            spq_s = int(o[p, q, s])
            sq_sp = int(o[q, s, p])
            inside = False
            for r in pts:
                if r == p or r == q:
                    continue
                if (int(o[s, p, r]) == ssp_q and
                        int(o[p, q, r]) == spq_s and
                        int(o[q, s, r]) == sq_sp):
                    inside = True
                    break
            empty[(p, q)] = not inside

    # ------------------------------------------------------------------
    # DP: G[(p, q)] = G(p, q, j; s)
    #
    # j=3 base case:
    #   G(p, q, 3; s) = 1  iff o[s,p,q]==+1 and empty(s,p,q)
    #
    # j>3 recursion:
    #   G(p, q, j; s) = Σ_{r in U_s: o[p,q,r]==+1, o[s,q,r]==+1}
    #                       G(q, r, j-1; s)
    #
    # Answer: Σ_{p,q: o[s,p,q]==+1} G(p, q, k-1; s)
    # ------------------------------------------------------------------
    G: dict[tuple[int, int], int] = {}
    for p in pts:
        for q in pts:
            if p == q:
                continue
            if int(o[s, p, q]) == 1 and empty.get((p, q), False):
                G[(p, q)] = 1

    if k == 3:
        return sum(G.values())

    for _j in range(4, k + 1):
        G_next: dict[tuple[int, int], int] = {}
        for p in pts:
            for q in pts:
                if p == q:
                    continue
                if int(o[s, p, q]) != 1:
                    continue
                # The triangle (s, p, q) must also be empty: the sub-polygon
                # s,...,q is extended by edge q→p, and the fan triangle △(s,p,q)
                # must not contain any other point.
                if not empty.get((p, q), False):
                    continue
                val = 0
                for r in pts:
                    if r == p or r == q:
                        continue
                    if int(o[p, q, r]) == 1 and int(o[s, q, r]) == 1:
                        val += G.get((q, r), 0)
                if val > 0:
                    G_next[(p, q)] = val
        G = G_next

    return sum(G.values())


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def count_empty_kgons_mrsw(sl: SmallLambda, k: int) -> int:
    """Count empty convex k-gons using the MRSW O(k·n³) algorithm.

    Works purely abstractly from the SmallLambda rank matrix — no coordinates.

    Each k-hole is counted exactly once (at its highest-index vertex in
    the natural labeling).
    """
    if k < 3:
        raise ValueError(f"k must be >= 3, got {k}")
    if sl.n < k:
        return 0

    # Apply natural labeling once
    hull_pts = sl.get_extremal_points()
    lab = sl.get_natural_labeling(hull_pts[0])
    bl = sl.relabeled(lab).to_big_lambda()
    o = bl.o

    total = 0
    for s in range(k - 1, sl.n):
        total += _count_kholes_anchor_s(o, s, k)

    return total


def count_all_kgons_mrsw(sl: SmallLambda, k_max: int = 6) -> dict:
    """Count empty convex k-gons for k = 3, 4, …, k_max in one pass."""
    if sl.n < 3:
        return {k: 0 for k in range(3, k_max + 1)}

    # Apply natural labeling once
    hull_pts = sl.get_extremal_points()
    lab = sl.get_natural_labeling(hull_pts[0])
    bl = sl.relabeled(lab).to_big_lambda()
    o = bl.o
    n = sl.n

    counts = {k: 0 for k in range(3, k_max + 1)}
    for s in range(2, n):
        for k in range(3, min(s + 2, k_max + 1)):
            counts[k] += _count_kholes_anchor_s(o, s, k)

    return counts
