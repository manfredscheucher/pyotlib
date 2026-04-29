"""Shared pytest fixtures for pyotlib2 tests."""

import pytest
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent


def _find_data_file(name: str) -> Path | None:
    search_dirs = [
        _REPO_ROOT / "old" / "pyotlib" / "scripts",
        _REPO_ROOT / "old" / "pyotlib" / "data",
        _REPO_ROOT / "old" / "pyotlib" / "sage_scripts",
        _REPO_ROOT / "data",
        _REPO_ROOT,
    ]
    for base in search_dirs:
        p = base / name
        if p.exists():
            return p
    return None


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "requires_data: test requires Aichholzer otypes database files"
    )


@pytest.fixture
def otypes_path():
    """Return a helper that finds otypes data files, skipping if not present."""
    def _get(n: int) -> Path:
        name = f"otypes{n:02d}.b08"
        p = _find_data_file(name)
        if p is None:
            pytest.skip(f"Data file {name} not found (download from Aichholzer)")
        return p
    return _get
