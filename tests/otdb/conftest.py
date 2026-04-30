"""Pytest fixtures for Graz order type database tests."""

import pytest
from pathlib import Path

_OTDB_ROOT = Path(__file__).parent


@pytest.fixture
def otypes_path():
    """Return a helper that finds otypes data files in tests/otdb/otypes/."""
    def _get(n: int) -> Path:
        ext = "b08" if n <= 8 else "b16"
        name = f"otypes{n:02d}.{ext}"
        p = _OTDB_ROOT / "otypes" / name
        if not p.exists():
            pytest.fail(f"Data file {name} not found — run tests/otdb/download.py first")
        return p
    return _get
