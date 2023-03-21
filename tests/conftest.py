"""Fixtures for testing."""
import pytest


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Automatically enable loading custom integrations in all tests."""
    yield
