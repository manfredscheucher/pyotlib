"""FelsnerMatrix: replace matrix encoding of an order type (Felsner 1997).

Given a SmallLambda in natural labeling (point 0 on the convex hull, remaining
points sorted CCW), the replace matrix M is an n×n binary matrix with:

    row_sum(i) = sum_j M[i,j] = n-1-i   for all i
    M[i,j] >= M[j,i]                     for all i < j

The encoding is a bijection between order types in natural labeling and valid
replace matrices.

Local sequence sigma_i
======================
For each line i, sigma_i is the permutation of [n]\\{i} giving the order in
which other lines cross line i (left to right in the wiring diagram).

Comparison rule (from the signotope): for x < y, x comes before y in sigma_i
iff o(sorted(i, x, y)) > 0, where o is the chirotope (BigLambda orientation).

The replace matrix bits
=======================
Define tau_i[k] = 1 if sigma_i[k] > i (k-th crossing of line i is with a
larger-indexed line), else 0.  Then:

    M[i,i] = tau_i[0]                         (diagonal: first crossing goes up?)
    M[i,j] = tau_i[rank_i(j) + 1]             if rank_i(j) < n-2
            = 0                                if rank_i(j) == n-2  (last crossing)

File formats
============
FelsnerText (.ft):   n rows of n space-separated bits (one OT per block).
FelsnerBinary (.fb): each row of M packed as ceil(n/8) bytes, MSB first.
                     For n bits, bit k of row i is M[i, n-1-k] in the LSB.
                     8 entries packed per byte → ceil(n²/8) bytes per OT.

Reference
=========
Felsner, S. (1997). On the number of arrangements of pseudolines.
In Proc. 12th Annual Symposium on Computational Geometry, pp. 30–37.
https://page.math.tu-berlin.de/~felsner/Paper/numarr.pdf

See also: arxiv:2303.04079 (Bergold, Felsner, Scheucher) for signotope terminology.
"""

from __future__ import annotations

import functools
import math

import numpy as np


class FelsnerMatrix:
    """Replace matrix (Felsner 1997) encoding an order type in natural labeling.

    Attributes
    ----------
    n : int
        Number of points.
    m : np.ndarray, shape (n, n), dtype int8
        Binary replace matrix.
    """

    def __init__(self, n: int, m: np.ndarray):
        assert m.shape == (n, n), f"expected shape ({n},{n}), got {m.shape}"
        assert m.dtype == np.int8
        self.n = n
        self.m = m

    # ------------------------------------------------------------------
    # Encoding: SmallLambda → FelsnerMatrix
    # ------------------------------------------------------------------

    @classmethod
    def from_small_lambda(cls, sl: "SmallLambda") -> "FelsnerMatrix":
        """Encode a SmallLambda in natural labeling as a FelsnerMatrix.

        The input must already be in natural labeling: L[0, j] = j-1 for
        j = 1, …, n-1.  Use ``sl.relabeled(sl.get_natural_labeling(p0))``
        first if needed.
        """
        n = sl.n
        bl = sl.to_big_lambda()
        o = bl.o

        # Verify natural labeling
        L = sl.get_l()
        for j in range(1, n):
            assert int(L[0, j]) == j - 1, (
                f"not in natural labeling: L[0,{j}]={int(L[0,j])}, expected {j-1}. "
                "Relabel first."
            )

        # Compute sigma_i for each i using the signotope comparison
        sigmas = [_compute_sigma_i(o, n, i) for i in range(n)]
        # rank_i[j] = position of j in sigma_i
        ranks = [{j: k for k, j in enumerate(s)} for s in sigmas]

        m = np.zeros((n, n), dtype=np.int8)
        for i in range(n):
            s = sigmas[i]
            # Diagonal: first element of sigma_i
            m[i, i] = np.int8(1 if s[0] > i else 0)
            for j in range(n):
                if j == i:
                    continue
                r = ranks[i][j]
                if r < n - 2:
                    m[i, j] = np.int8(1 if s[r + 1] > i else 0)
                # else: r == n-2 (last element), M[i,j] = 0 (default)
        return cls(n, m)

    # ------------------------------------------------------------------
    # Decoding: FelsnerMatrix → SmallLambda
    # ------------------------------------------------------------------

    def to_small_lambda(self) -> "SmallLambda":
        """Decode the replace matrix back to a SmallLambda in natural labeling.

        Algorithm (Felsner 1997, proof of Lemma 1)
        -------------------------------------------
        1. Sweep M with the wiring-diagram algorithm to reconstruct
           the chirotope-based local sequences sigma_i (sigma_chi).
        2. From sigma_chi, reconstruct the chirotope o:
               for a < b < c,  o[a,b,c] = +1  iff  b comes before c in sigma_a.
        3. Compute L from o:  L[i,j] = #{k : o(i,j,k) = +1}.
        4. Return SmallLambda(n, L).

        The sigma produced by the sweep matches the sigma used during encoding,
        so re-encoding the resulting L gives back this matrix exactly.
        """
        from pyotlib2.core.small_lambda import SmallLambda

        n = self.n
        m = self.m

        # ---- Step 1: wiring-diagram sweep → sigma_chi ----
        # perm[pos] = line ID at position pos; starts identity
        perm = list(range(n))
        # cross[line] = number of crossings already done by that line
        cross = [0] * n
        # sigma[i] = crossing sequence of line i (in order)
        sigma = [[] for _ in range(n)]

        def _tau(line: int, k: int) -> int:
            """tau_i[k]: 1 if k-th crossing of line i is with a larger-indexed line."""
            if k == 0:
                return int(m[line, line])
            return int(m[line, sigma[line][k - 1]])

        total = n * (n - 1) // 2
        for _ in range(total):
            # Find leftmost "10" pattern in the current bit state
            pos = -1
            for p in range(n - 1):
                if _tau(perm[p], cross[perm[p]]) == 1 and _tau(perm[p + 1], cross[perm[p + 1]]) == 0:
                    pos = p
                    break
            if pos < 0:
                raise ValueError(
                    "FelsnerMatrix.to_small_lambda: no '10' pattern found — "
                    "matrix may not be a valid replace matrix."
                )
            a = perm[pos]
            b = perm[pos + 1]
            sigma[a].append(b)
            sigma[b].append(a)
            cross[a] += 1
            cross[b] += 1
            perm[pos], perm[pos + 1] = b, a

        # ---- Step 2: reconstruct chirotope from sigma_chi ----
        # For a < b < c: o[a,b,c] = +1 iff b comes before c in sigma_a
        # (this is exactly the formula used by _compute_sigma_i / from_small_lambda)
        rank = [[0] * n for _ in range(n)]  # rank[i][j] = position of j in sigma_i
        for i in range(n):
            for k, j in enumerate(sigma[i]):
                rank[i][j] = k

        o = np.zeros((n, n, n), dtype=np.int8)
        for a in range(n):
            for b in range(a + 1, n):
                for c in range(b + 1, n):
                    # b before c in sigma_a iff o[a,b,c] = +1
                    val = np.int8(1) if rank[a][b] < rank[a][c] else np.int8(-1)
                    # fill all 6 permutations via antisymmetry
                    o[a, b, c] = val
                    o[a, c, b] = -val
                    o[b, a, c] = -val
                    o[b, c, a] = val
                    o[c, a, b] = val
                    o[c, b, a] = -val

        # ---- Step 3: compute L from chirotope ----
        # L[i,j] = #{k : o(i,j,k) = +1}
        L = np.zeros((n, n), dtype=np.int32)
        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                count = 0
                for k in range(n):
                    if k == i or k == j:
                        continue
                    # o(i,j,k): sign depends on permutation (i,j,k) vs sorted order
                    triple = sorted([i, j, k])
                    perm_sign = _perm_sign(i, j, k, triple)
                    val = int(o[triple[0], triple[1], triple[2]]) * perm_sign
                    if val == 1:
                        count += 1
                L[i, j] = count

        return SmallLambda(n, L)

    # ------------------------------------------------------------------
    # Serialisation: FelsnerText (.ft)
    # ------------------------------------------------------------------

    def to_fmt_string(self) -> str:
        """Serialize to FelsnerMatrix text (.fmt): n rows of n space-separated bits."""
        return (
            "\n".join(
                " ".join(str(int(self.m[i, j])) for j in range(self.n))
                for i in range(self.n)
            )
            + "\n"
        )

    @staticmethod
    def from_fmt_string(n: int, s: str) -> "FelsnerMatrix":
        """Parse FelsnerMatrix text (.fmt) format."""
        m = np.zeros((n, n), dtype=np.int8)
        lines = [ln for ln in s.strip().split("\n") if ln.strip()]
        assert len(lines) == n, f"expected {n} lines, got {len(lines)}"
        for i, line in enumerate(lines):
            parts = line.split()
            assert len(parts) == n, f"line {i}: expected {n} bits, got {len(parts)}"
            for j, p in enumerate(parts):
                m[i, j] = np.int8(int(p))
        return FelsnerMatrix(n, m)

    # ------------------------------------------------------------------
    # Serialisation: FelsnerMatrix binary (.fmb)
    # ------------------------------------------------------------------

    def to_fmb_bytes(self) -> bytes:
        """Serialize to FelsnerMatrix binary (.fmb): n² bits, MSB-first.

        Row-major order: M[0,0], M[0,1], …, M[n-1,n-1].
        Packed into ceil(n²/8) bytes, zero-padded.
        """
        bits = [int(self.m[i, j]) for i in range(self.n) for j in range(self.n)]
        n_bytes = math.ceil(len(bits) / 8)
        result = bytearray(n_bytes)
        for k, bit in enumerate(bits):
            if bit:
                result[k // 8] |= 1 << (7 - k % 8)
        return bytes(result)

    @staticmethod
    def from_fmb_bytes(n: int, data: bytes) -> "FelsnerMatrix":
        """Deserialize from FelsnerMatrix binary (.fmb) format."""
        n2 = n * n
        expected = math.ceil(n2 / 8)
        assert len(data) == expected, (
            f"expected {expected} bytes for n={n}, got {len(data)}"
        )
        m = np.zeros((n, n), dtype=np.int8)
        for k in range(n2):
            bit = (data[k // 8] >> (7 - k % 8)) & 1
            i, j = divmod(k, n)
            m[i, j] = np.int8(bit)
        return FelsnerMatrix(n, m)

    # ------------------------------------------------------------------
    # Comparison / repr
    # ------------------------------------------------------------------

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FelsnerMatrix):
            return NotImplemented
        return self.n == other.n and np.array_equal(self.m, other.m)

    def __repr__(self) -> str:
        return f"FelsnerMatrix(n={self.n})"


# ------------------------------------------------------------------
# Internal helper: compute sigma_i
# ------------------------------------------------------------------

def _compute_sigma_i(o: np.ndarray, n: int, i: int) -> list:
    """Compute the local sequence sigma_i from the chirotope o.

    For x < y (both in [n]\\{i}), x comes before y in sigma_i iff
    o(sorted(i, x, y)) > 0.  This gives a total linear order on [n]\\{i}
    for non-degenerate order types in natural labeling.

    Parameters
    ----------
    o : np.ndarray, shape (n, n, n), dtype int8
        Chirotope: o[a, b, c] in {-1, 0, +1} for a < b < c.
    n : int
        Number of points.
    i : int
        The line index whose local sequence we compute.

    Returns
    -------
    list of int
        Permutation of [n]\\{i} in crossing order on line i.
    """
    others = [j for j in range(n) if j != i]

    def cmp(x: int, y: int) -> int:
        if x == y:
            return 0
        a, b = (x, y) if x < y else (y, x)
        triple = sorted([i, a, b])
        sign = int(o[triple[0], triple[1], triple[2]])
        # a < b: a before b iff sign > 0
        if x < y:
            return -1 if sign > 0 else 1
        else:
            return 1 if sign > 0 else -1

    return sorted(others, key=functools.cmp_to_key(cmp))


def _perm_sign(i: int, j: int, k: int, triple: list) -> int:
    """Return the sign of the permutation mapping (i,j,k) to sorted triple.

    Returns +1 if (i,j,k) is an even permutation of triple, -1 if odd.
    Used to evaluate o(i,j,k) from the stored o[a,b,c] with a<b<c.
    """
    a, b, c = triple
    # Enumerate all 6 permutations of (a,b,c) and their signs
    if (i, j, k) == (a, b, c):
        return 1
    if (i, j, k) == (b, c, a):
        return 1
    if (i, j, k) == (c, a, b):
        return 1
    # odd permutations
    return -1
