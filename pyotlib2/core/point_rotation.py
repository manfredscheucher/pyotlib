"""Helper for rotating/reflecting point sets used by BigLambda.from_flips."""

from __future__ import annotations


def rotate_by_flip(points: list, F: list) -> list:
    """Reflect each point i where F[i] == 1 through the origin (negate coordinates)."""
    return [(-x, -y) if F[i] else (x, y) for i, (x, y) in enumerate(points)]
