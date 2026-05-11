"""Grassmann-Plücker realizability test via GLPK linear programming.

Generates an LP that is feasible iff the order type is realizable.
A solution with myEps > 0 witnesses realizability (unbounded); if the
LP is infeasible (GLPK primal+dual status both 2), the OT is non-realizable.

Requires the ``glpsol`` binary (GLPK package) to be on PATH.

Reference: Grassmann-Plücker relations for rank-3 oriented matroids.
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
    """Tests realizability via a Grassmann-Plücker LP solved with GLPK.

    The LP maximises a slack variable myEps subject to:
      - myEps >= 0
      - o_abc >= 0  for all triples (a,b,c) with a<b<c
      - For each 5-tuple (a,b,c,d,e) with b<c,d,e and the right sign pattern,
        two GP constraints of the form:
          o_abc + o_ade - o_abd - o_ace + myEps <= 0
          o_abe + o_acd - o_abd - o_ace + myEps <= 0

    If the optimum myEps > 0 the LP is unbounded → realizable.
    If the LP is infeasible → non-realizable (GLPK primal+dual status = 2).
    Otherwise → undecided.
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
            lp_path  = os.path.join(tmpdir, "ot.lp")
            sol_path = os.path.join(tmpdir, "ot.sol")
            self._write_lp(ot, lp_path)
            return self._solve(lp_path, sol_path)

    # ------------------------------------------------------------------
    # LP generation  (ported from old pyotlib GPRealizationTester)
    # ------------------------------------------------------------------

    def _write_lp(self, ot: SmallLambda, path: str) -> None:
        n = ot.n
        o_arr = ot.to_big_lambda().o

        def var(i, j, k):
            a, b, c = sorted([i, j, k])
            return f"o_{a}_{b}_{c}"

        lines = [
            "/* Grassmann-Plucker LP for realizability */",
            "Maximize",
            " obj: 1 myEps",
            "Subject To",
            " pos_myeps: myEps >= 0",
        ]

        # positivity constraints for each triple
        for a, b, c in combinations(range(n), 3):
            lines.append(f" pos_{a}_{b}_{c}: {var(a,b,c)} >= 0")

        # Grassmann-Plucker constraints
        # For each (a,b) and each permutation (c,d,e) of {b+1..n-1}:
        # if all three products o[a,b,c]*o[a,d,e], o[a,b,d]*o[a,c,e], o[a,b,e]*o[a,c,d] > 0
        # then add two GP inequalities.
        ct = 0
        for a, b in permutations(range(n), 2):
            for c, d, e in permutations(range(b + 1, n), 3):
                if (    o_arr[a, b, c] * o_arr[a, d, e] > 0
                    and o_arr[a, b, d] * o_arr[a, c, e] > 0
                    and o_arr[a, b, e] * o_arr[a, c, d] > 0):
                    ct += 1
                    lines.append(
                        f" c{2*ct}: {var(a,b,c)} +{var(a,d,e)} -{var(a,b,d)} -{var(a,c,e)} + myEps <= 0"
                    )
                    lines.append(
                        f" c{2*ct+1}: {var(a,b,e)} +{var(a,c,d)} -{var(a,b,d)} -{var(a,c,e)} + myEps <= 0"
                    )

        assert ct == 5 * binomial(n, 5), f"expected {5*binomial(n,5)} GP constraints, got {ct}"

        lines.append("End")

        with open(path, "w") as f:
            f.write("\n".join(lines) + "\n")

    # ------------------------------------------------------------------
    # Solve and parse
    # ------------------------------------------------------------------

    def _solve(self, lp_path: str, sol_path: str) -> bool:
        cmd = ["glpsol", "--lp", lp_path, "--write", sol_path, "--xcheck"]
        if self.use_dual_simplex:
            cmd.append("--dual")
        if self.time_limit > 0:
            cmd += ["--tmlim", str(self.time_limit)]

        subprocess.run(cmd, capture_output=True)

        # Parse GLPK solution file: line 2 is "statusP statusD opt_value"
        # statusP == 2 and statusD == 2  →  infeasible  →  non-realizable
        try:
            with open(sol_path) as f:
                f.readline()
                line2 = f.readline()
            status_p, status_d, *_ = line2.split()
            if status_p == "2" and status_d == "2":
                return False  # infeasible → non-realizable
        except (FileNotFoundError, ValueError):
            pass

        raise Undecided("GLPK did not produce a conclusive result")
