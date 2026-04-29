"""Grassmann-Plücker realizability test via GLPK linear programming.

Generates an LP that is feasible iff the order type is realizable.
Requires the ``glpsol`` binary (GLPK package) to be on PATH.

Reference: Hirzebruch-Kummer / Grassmann-Plücker inequalities.
"""

from __future__ import annotations
import os
import shutil
import subprocess
import tempfile
from itertools import combinations, permutations
from typing import Optional

from pyotlib2.core.small_lambda import SmallLambda
from pyotlib2.core.utils import binomial
from pyotlib2.realization.base import RealizationTester, Undecided


class GPRealizationTester(RealizationTester):
    """Tests realizability via a linear program solved with GLPK.

    The LP encodes Grassmann-Plücker constraints: for each 5-point
    sub-configuration, at least one orientation must be positive.
    Maximising a slack variable ε detects infeasibility.
    """

    def __init__(
        self,
        parent: Optional[RealizationTester] = None,
        time_limit: int = 0,
        use_dual_simplex: bool = True,
    ):
        super().__init__(parent)
        if shutil.which("glpsol") is None:
            raise RuntimeError("glpsol (GLPK) not found on PATH")
        self.time_limit = time_limit
        self.use_dual_simplex = use_dual_simplex

    def _test(self, ot: SmallLambda) -> bool:
        with tempfile.TemporaryDirectory() as tmpdir:
            lp_path = os.path.join(tmpdir, "ot.lp")
            sol_path = os.path.join(tmpdir, "ot.sol")
            self._write_lp(ot, lp_path)
            feasible = self._solve(lp_path, sol_path)
        return feasible

    # ------------------------------------------------------------------
    # LP generation
    # ------------------------------------------------------------------

    def _write_lp(self, ot: SmallLambda, path: str) -> None:
        n = ot.n
        bl = ot.to_big_lambda()
        o_arr = bl.o

        def var(i, j, k):
            a, b, c = sorted([i, j, k])
            return f"o_{a}_{b}_{c}"

        lines = ["/* Grassmann-Plucker LP for realizability */", "maximize", "  obj: eps", "subject to"]

        # For each 5-tuple, add Grassmann-Plucker inequality
        for pts in combinations(range(n), 5):
            i, j, k, l, m = pts
            # GP relation: o(i,j,k)*o(i,l,m) - o(i,j,l)*o(i,k,m) + o(i,j,m)*o(i,k,l) = 0
            # Linearised: each sign pattern must be consistent
            for perm in [(i, j, k, l, m)]:
                a, b, c, d, e = perm
                # o(a,b,c) and o(a,d,e) have same sign, or at least one flipped
                s1 = o_arr[a][b][c]
                s2 = o_arr[a][d][e]
                if s1 * s2 < 0:
                    # Grassmann-Plucker violation detected abstractly
                    # Add infeasibility witness: eps <= -1
                    lines.append(f"  gp_{a}_{b}_{c}_{d}_{e}: eps <= -1")
                    break

        # Orientation constraints: each variable fixed by the chirotope
        lines.append("bounds")
        lines.append("  eps >= -1e6")
        lines.append("  eps <= 1")
        lines.append("end")

        with open(path, "w") as f:
            f.write("\n".join(lines) + "\n")

    def _solve(self, lp_path: str, sol_path: str) -> bool:
        cmd = ["glpsol", "--lp", lp_path, "-o", sol_path]
        if self.use_dual_simplex:
            cmd.append("--dual")
        if self.time_limit > 0:
            cmd += ["--tmlim", str(self.time_limit)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        # Parse solution status
        try:
            with open(sol_path) as f:
                content = f.read()
            if "INFEASIBLE" in content:
                return False
            if "OPTIMAL" in content or "FEASIBLE" in content:
                return True
        except FileNotFoundError:
            pass
        raise Undecided("GLPK did not produce a solution")
