"""Define test fixtures for Blue Current."""

from typing import Any

import pytest
from homeassistant.components.blue_current.const import (
    DELAYED_CHARGING,
    DOMAIN,
    PLUG_AND_CHARGE,
    PRICE_BASED_CHARGING,
    PUBLIC_CHARGING,
    SMART_CHARGING,
)

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
    """Define a charge point fixture."""
    return {
        "evse_id": "101",
        "model_type": "",
        "name": "",
        "activity": "available",
        SMART_CHARGING: False,
        PLUG_AND_CHARGE: {"value": False, "permission": "write"},
        PUBLIC_CHARGING: {"value": True, "permission": "write"},
        DELAYED_CHARGING: {"value": True},
        PRICE_BASED_CHARGING: {"value": False},
    }


@pytest.fixture(name="price_based_charging_charge_point")
def price_based_charging_charge_point_fixture() -> dict[str, Any]:
    """Define a charge point fixture."""
    return {
        "evse_id": "101",
        "model_type": "",
        "name": "",
        "activity": "available",
        SMART_CHARGING: True,
        PLUG_AND_CHARGE: {"value": False, "permission": "write"},
        PUBLIC_CHARGING: {"value": True, "permission": "write"},
        DELAYED_CHARGING: {"value": False},
        PRICE_BASED_CHARGING: {"value": True},
    }


@pytest.fixture(name="delayed_charging_charge_point")
def delayed_charging_charge_point_fixture() -> dict[str, Any]:
    """Define a charge point fixture."""
    return {
        "evse_id": "101",
        "model_type": "",
        "name": "",
        "activity": "available",
        SMART_CHARGING: True,
        PLUG_AND_CHARGE: {"value": False, "permission": "write"},
        PUBLIC_CHARGING: {"value": True, "permission": "write"},
        DELAYED_CHARGING: {"value": True},
        PRICE_BASED_CHARGING: {"value": False},
    }


@pytest.fixture(name="smart_charging_no_profile_charge_point")
def smart_charging_no_profile_charge_point_fixture() -> dict[str, Any]:
    """Define a charge point fixture."""
    return {
        "evse_id": "101",
        "model_type": "",
        "name": "",
        "activity": "available",
        SMART_CHARGING: True,
        PLUG_AND_CHARGE: {"value": False, "permission": "write"},
        PUBLIC_CHARGING: {"value": True, "permission": "write"},
        DELAYED_CHARGING: {"value": False},
        PRICE_BASED_CHARGING: {"value": False},
    }
