"""Shared pytest configuration and fixtures."""

import os

import pytest

from src.core.event_store import EventStore
from tests.fixtures import build_synthetic_store

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture
def synthetic_store() -> EventStore:
    return build_synthetic_store()

