"""Shared pytest fixtures for pyotlib2 tests."""

import pytest


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "requires_data: test requires Graz order type database files"
    )
