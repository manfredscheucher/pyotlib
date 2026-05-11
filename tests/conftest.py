"""Shared pytest fixtures for pyotlib2 tests."""

import pytest


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "requires_data: test requires Graz order type database files"
    )
    config.addinivalue_line(
        "markers", "slow: test takes a long time (run with: pytest -m slow)"
    )
