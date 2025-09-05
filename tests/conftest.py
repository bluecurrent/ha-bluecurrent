"""Define test fixtures for Blue Current."""

import pytest

from homeassistant.components.blue_current.const import DOMAIN, SMART_CHARGING, PLUG_AND_CHARGE, PUBLIC_CHARGING, \
    DELAYED_CHARGING, PRICE_BASED_CHARGING

from tests.common import MockConfigEntry


@pytest.fixture(name="config_entry")
def config_entry_fixture() -> MockConfigEntry:
    """Define a config entry fixture."""
    return MockConfigEntry(
        domain=DOMAIN,
        entry_id="uuid",
        unique_id="1234",
        data={"api_token": "123"},
    )

@pytest.fixture(name="charge_point")
def charge_point_fixture() -> dict[str, Any]:
    """Define a charge point fixture"""
    return {
    "evse_id": "101",
    "model_type": "",
    "name": "",
    "activity": "available",
    SMART_CHARGING: False,
    PLUG_AND_CHARGE: {"value": False, "permission": "write"},
    PUBLIC_CHARGING: {"value": True, "permission": "write"},
    DELAYED_CHARGING: {"value": True},
    PRICE_BASED_CHARGING: {"value": False}
}
