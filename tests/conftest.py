"""Shared test fixtures for the goal_watcher test suite."""

import pytest


@pytest.fixture(autouse=True)
def faker_seed() -> int:
    return 12345
