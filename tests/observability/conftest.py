"""Shared fixtures for observability tests."""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _reset_phoenix_initialization():
    """Allow setup_observability() to run fresh in each test."""
    import observability.phoenix as phoenix

    phoenix._initialized = False
    yield
    phoenix._initialized = False
