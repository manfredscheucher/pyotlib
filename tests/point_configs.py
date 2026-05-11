"""Well-known point configurations for testing.

All functions return a SmallLambda with realization attached (unless noted).
Use .to_abstract() or SmallLambda.from_string() if you need an abstract-only OT.

Available configurations
------------------------
convex_position_moment_curve(n)   -- moment curve (i, i²), always general position
convex_position_circle(n)         -- regular n-gon on circle, R doubled until all-+ OT
horton_set(k)                     -- Horton set of size 2^(k+1) (no empty convex hexagon)
one_interior(n=5)                 -- (n-1) points on convex hull + 1 interior point
abstract_only(sl)                 -- strip realization from a SmallLambda

PoSeZo singletons (https://www.eurogiga-compose.eu/posezo.php)
--------------------------------------------------------------
PoSeZo.n10_c1_1_convex_5_hole        -- 10 pts, exactly 1 convex 5-hole, hull=5
PoSeZo.n12_c1_min_convex_3_4_5_holes -- 12 pts, min 3/4/5-holes: 94/42/3
PoSeZo.n12_c1_min_crossing_number_153 -- 12 pts, rectilinear crossing number = 153
PoSeZo.n13_c1_min_convex_3_4_5_holes -- 13 pts, min 3/4/5-holes: 114/51/3
PoSeZo.n14_c1_6_convex_5_holes       -- 14 pts, exactly 6 convex 5-holes
PoSeZo.n15_c1_9_convex_5_holes       -- 15 pts, exactly 9 convex 5-holes
PoSeZo.n29_c1_no_convex_6_hole       -- 29 pts, no convex 6-hole (151 convex 5-holes)
"""

from __future__ import annotations
from pyotlib2.core.point_set import PointSet
from pyotlib2.core.small_lambda import SmallLambda


def convex_position_moment_curve(n: int) -> SmallLambda:
    """n points on the moment curve: (i, i²) for i = 1..n.

    Always in general position (no 3 collinear), all triples have the same
    orientation sign — this is the all-convex OT.
    """
    pts = [(i, i * i) for i in range(1, n + 1)]
    return PointSet(n, pts).to_small_lambda(lazy=False)


def convex_position_circle(n: int) -> SmallLambda:
    """n points on a circle with radius R, doubled until the OT is all-convex.

    Starts at R=2 and doubles until rounding errors don't create collinear
    triples or wrong orientations.  Returns the first valid all-+ OT.
    """
    import math
    R = 2
    while True:
        pts = [
            (round(R * math.cos(2 * math.pi * i / n)),
             round(R * math.sin(2 * math.pi * i / n)))
            for i in range(n)
        ]
        ps = PointSet(n, pts)
        if ps.has_collinear_points():
            R *= 2
            continue
        sl = ps.to_small_lambda(lazy=False)
        bl = sl.to_big_lambda()
        # check all triples are +1 (all-convex)
        from itertools import combinations
        if all(bl.o[a, b, c] == 1
               for a, b, c in combinations(range(n), 3)):
            return sl
        R *= 2


def horton_set(k: int) -> SmallLambda:
    """Horton set of size n = 2^(k+1), constructed recursively.

    The Horton set is a classical point configuration with no empty convex
    hexagon.  Recursive construction: split into two halves H0, H1;
    scale and interleave them.

    k=0 → 2 points, k=1 → 4 points, k=2 → 8 points, etc.

    Reference: Horton (1983) — no empty convex hexagons in the plane.
    """
    def _horton(k: int) -> list[tuple[int, int]]:
        if k == 0:
            return [(0, 0), (1, 0)]
        H = _horton(k - 1)
        m = len(H)
        # scale x by 2, then interleave H0 (even x) and H1 (odd x + perturbation)
        H0 = [(2 * x, 2 * y) for x, y in H]
        H1 = [(2 * x + 1, 2 * y + (1 if i % 2 == 0 else -1))
              for i, (x, y) in enumerate(H)]
        return H0 + H1

    pts = _horton(k)
    n = len(pts)
    # normalize to positive coords
    xmin = min(x for x, y in pts)
    ymin = min(y for x, y in pts)
    pts = [(x - xmin, y - ymin) for x, y in pts]
    ps = PointSet(n, pts)
    return ps.to_small_lambda(lazy=False)


def one_interior(n: int = 5) -> SmallLambda:
    """n points: (n-1) in convex position + 1 interior point.

    Uses the moment curve for the hull and places the interior point
    near the centroid, trying small offsets until we find a valid interior point
    (no collinearity and hull size = n-1).
    """
    hull = [(i, i * i) for i in range(1, n)]
    cx = sum(x for x, y in hull) // (n - 1)
    cy = sum(y for x, y in hull) // (n - 1)
    # try small offsets until we find a genuine interior point
    for dx in range(-n, n + 1):
        for dy in range(-n, n + 1):
            candidate = (cx + dx, cy + dy)
            if candidate in hull:
                continue
            pts = hull + [candidate]
            ps = PointSet(n, pts)
            if ps.has_collinear_points():
                continue
            sl = ps.to_small_lambda(lazy=False)
            bl = sl.to_big_lambda()
            if len(bl.onion[0]) == n - 1:
                return sl
    raise RuntimeError(f"could not find interior point for one_interior(n={n})")


def abstract_only(sl: SmallLambda) -> SmallLambda:
    """Return a copy of sl with the realization stripped (abstract-only)."""
    return SmallLambda.from_string(sl.n, sl.to_string())


# ---------------------------------------------------------------------------
# PoSeZo singletons
# ---------------------------------------------------------------------------

class PoSeZo:
    """Named PoSeZo singleton configurations.

    Coordinates are taken directly from the PoSeZo database:
    https://www.eurogiga-compose.eu/posezo.php

    Each class method returns a SmallLambda with realization attached.
    """

    @staticmethod
    def n10_c1_1_convex_5_hole() -> SmallLambda:
        """10-point set with exactly 1 convex 5-hole and convex hull of size 5.

        Source: https://www.eurogiga-compose.eu/posezo/n10_c1_1_convex_5_hole/
        Known properties: convex 5-holes = 1, hull = 5
        """
        pts = [
            (42792, 20304),
            (12156, 0),
            (0, 44412),
            (27110, 29396),
            (21312, 33564),
            (35052, 25200),
            (28260, 45984),
            (34200, 39360),
            (27648, 61512),
            (62400, 53640),
        ]
        return PointSet(10, pts).to_small_lambda(lazy=False)

    @staticmethod
    def n12_c1_min_convex_3_4_5_holes() -> SmallLambda:
        """12-point set minimizing 3/4/5-holes: 94 / 42 / 3.

        Source: https://www.eurogiga-compose.eu/posezo/n12_c1_min_convex_3_4_5_holes/
        Known properties: 3-holes = 94, 4-holes = 42, 5-holes = 3
        Reference: Aichholzer et al., CCCG 2012
        """
        pts = [
            (0, 0),
            (100, 0),
            (50, 87),
            (50, 38),
            (55, 32),
            (53, 19),
            (47, 19),
            (45, 32),
            (41, 4),
            (59, 4),
            (25, 40),
            (75, 40),
        ]
        return PointSet(12, pts).to_small_lambda(lazy=False)

    @staticmethod
    def n12_c1_min_crossing_number_153() -> SmallLambda:
        """12-point set with rectilinear crossing number 153 (unique minimum).

        Source: https://www.eurogiga-compose.eu/posezo/n12_c1_min_crossing_number_153/
        Known properties: crossings = 153
        """
        pts = [
            (13290, 30827),
            (45233, 24125),
            (10217, 11859),
            (6294, 0),
            (0, 49579),
            (13699, 33996),
            (2314, 46508),
            (16411, 17184),
            (29175, 22801),
            (52500, 24275),
            (24447, 26182),
            (8784, 6906),
        ]
        return PointSet(12, pts).to_small_lambda(lazy=False)

    @staticmethod
    def n13_c1_min_convex_3_4_5_holes() -> SmallLambda:
        """13-point set minimizing 3/4/5-holes: 114 / 51 / 3.

        Source: https://www.eurogiga-compose.eu/posezo/n13_c1_min_convex_3_4_5_holes/
        Known properties: 3-holes = 114, 4-holes = 51, 5-holes = 3
        Created by Thomas Hackl, derived from Manfred Scheucher's Bachelor thesis.
        """
        pts = [
            (160, 7359),
            (1768, 6530),
            (2592, 6679),
            (4239, 6383),
            (3955, 5593),
            (2960, 5759),
            (2338, 4960),
            (2880, 4320),
            (2960, 2520),
            (5759, 7359),
            (3076, 5497),
            (2684, 5783),
            (3113, 5976),
        ]
        return PointSet(13, pts).to_small_lambda(lazy=False)

    @staticmethod
    def n14_c1_6_convex_5_holes() -> SmallLambda:
        """14-point set with 6 convex 5-holes.

        Source: https://www.eurogiga-compose.eu/posezo/n14_c1_6_convex_5_holes/
        Known properties: convex 5-holes = 6
        """
        pts = [
            (0, 64677),
            (65280, 65280),
            (32144, 56115),
            (38443, 42292),
            (29486, 47302),
            (28031, 47507),
            (28497, 46248),
            (26495, 45981),
            (26324, 45249),
            (19359, 44531),
            (3957, 0),
            (22031, 40206),
            (5222, 32611),
            (48433, 51953),
        ]
        return PointSet(14, pts).to_small_lambda(lazy=False)

    @staticmethod
    def n15_c1_9_convex_5_holes() -> SmallLambda:
        """15-point set with 9 convex 5-holes (minimum known for n=15).

        Source: https://www.eurogiga-compose.eu/posezo/n15_c1_9_convex_5_holes/
        Known properties: convex 5-holes = 9
        """
        pts = [
            (0, 62035),
            (65280, 65280),
            (29017, 42686),
            (28073, 43222),
            (27580, 43180),
            (27723, 42707),
            (26856, 42289),
            (26977, 42113),
            (24450, 40872),
            (24201, 38628),
            (18887, 0),
            (29771, 62134),
            (52452, 63860),
            (12179, 28100),
            (42831, 62949),
        ]
        return PointSet(15, pts).to_small_lambda(lazy=False)

    @staticmethod
    def n29_c1_no_convex_6_hole() -> SmallLambda:
        """29-point set with no convex 6-hole; has 151 convex 5-holes.

        Currently largest known set without a convex 6-hole.
        Source: https://www.eurogiga-compose.eu/posezo/n29_c1_no_convex_6_hole/
        Known properties: 5-holes = 151, 6-holes = 0
        Original source: Overmars (Utrecht University)
        """
        pts = [
            (436, 535), (434, 552), (453, 542), (410, 539), (392, 575),
            (416, 550), (426, 526), (366, 552), (446, 565), (458, 526),
            (489, 537), (374, 525), (449, 518), (492, 502), (396, 613),
            (306, 592), (450, 498), (371, 487), (552, 502), (496, 579),
            (310, 531), (754, 697), (516, 467), (22, 531), (16, 743),
            (777, 194), (1, 1260), (1259, 320), (37, 0),
        ]
        return PointSet(29, pts).to_small_lambda(lazy=False)
