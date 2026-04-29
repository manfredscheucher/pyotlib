"""Utility math functions used throughout pyotlib2."""

from math import gcd as _gcd
from fractions import Fraction


def sign(x) -> int:
    """Return -1, 0, or 1 depending on the sign of x."""
    if x > 0:
        return 1
    if x < 0:
        return -1
    return 0


def binomial(n: int, k: int) -> int:
    """Binomial coefficient C(n, k)."""
    if k < 0 or k > n:
        return 0
    if k == 0 or k == n:
        return 1
    k = min(k, n - k)
    result = 1
    for i in range(k):
        result = result * (n - i) // (i + 1)
    return result


def lcm(*xs: int) -> int:
    """Least common multiple of one or more integers."""
    result = abs(xs[0])
    for x in xs[1:]:
        result = result * abs(x) // _gcd(result, abs(x))
    return result


def ceil_log2(x: int) -> int:
    """Return ceil(log2(x))."""
    b, xmax = 0, 1
    while x > xmax:
        b += 1
        xmax *= 2
    return b


def invert_perm(perm: list) -> list:
    """Return the inverse of a permutation."""
    inv = [0] * len(perm)
    for i, p in enumerate(perm):
        inv[p] = i
    return inv


def concat_perms(perm1: list, perm2: list) -> list:
    """Return perm1 composed with perm2: result[i] = perm1[perm2[i]]."""
    return [perm1[i] for i in perm2]
