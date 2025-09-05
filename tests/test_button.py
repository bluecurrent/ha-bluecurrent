"""The tests for Blue Current buttons."""
from typing import Any

import pytest
from syrupy.assertion import SnapshotAssertion

from homeassistant.components.blue_current.const import (
    DELAYED_CHARGING,
    PRICE_BASED_CHARGING,
    SMART_CHARGING,
    VALUE, ACTIVITY, DELAYED, CHARGING,
)
from homeassistant.components.button import DOMAIN as BUTTON_DOMAIN, SERVICE_PRESS
from homeassistant.const import ATTR_ENTITY_ID, STATE_UNKNOWN, Platform, STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from tests.common import MockConfigEntry, snapshot_platform
from . import init_integration

charge_point_buttons = [
    "stop_charge_session",
    "reset",
    "reboot",
    "boost_charge_session",
]


async def test_buttons_created(
    hass: HomeAssistant,
    snapshot: SnapshotAssertion,
    config_entry: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test if all buttons are created."""
    await init_integration(hass, config_entry, Platform.BUTTON)

    await snapshot_platform(hass, entity_registry, snapshot, config_entry.entry_id)


@pytest.mark.freeze_time("2023-01-13 12:00:00+00:00")
async def test_charge_point_buttons(
    hass: HomeAssistant, config_entry: MockConfigEntry, charge_point: dict[str, Any]
) -> None:
    """Test the underlying charge point buttons."""
    # To test the boost button, set the activity to delayed and smart charging to true.
    charge_point[SMART_CHARGING] = True
    charge_point[ACTIVITY] = DELAYED

    await init_integration(hass, config_entry, Platform.BUTTON, charge_point)

    for button in charge_point_buttons:
        state = hass.states.get(f"button.101_{button}")
        assert state is not None
        assert state.state == STATE_UNKNOWN

        await hass.services.async_call(
            BUTTON_DOMAIN,
            SERVICE_PRESS,
            {ATTR_ENTITY_ID: f"button.101_{button}"},
            blocking=True,
        )

        state = hass.states.get(f"button.101_{button}")
        assert state
        assert state.state == "2023-01-13T12:00:00+00:00"

async def test_boost_price_based_charging(hass: HomeAssistant, config_entry: MockConfigEntry, charge_point: dict[str, Any]) -> None:
    charge_point[SMART_CHARGING] = True
    charge_point[PRICE_BASED_CHARGING][VALUE] = True
    charge_point[DELAYED_CHARGING][VALUE] = False
    charge_point[ACTIVITY] = CHARGING

    integration = await init_integration(hass, config_entry, Platform.BUTTON, charge_point)
    client = integration[0]

    await hass.services.async_call(
        BUTTON_DOMAIN,
        SERVICE_PRESS,
        {ATTR_ENTITY_ID: "button.101_boost_charge_session"},
        blocking=True,
    )

    client.override_price_based_charging_profile.assert_called_once()
    client.override_delayed_charging_profile.assert_not_called()

async def test_boost_delayed_charging(hass: HomeAssistant, config_entry: MockConfigEntry, charge_point: dict[str, Any]) -> None:
    charge_point[SMART_CHARGING] = True
    charge_point[ACTIVITY] = DELAYED

    integration = await init_integration(hass, config_entry, Platform.BUTTON, charge_point)
    client = integration[0]

    await hass.services.async_call(
        BUTTON_DOMAIN,
        SERVICE_PRESS,
        {ATTR_ENTITY_ID: "button.101_boost_charge_session"},
        blocking=True,
    )

    client.override_delayed_charging_profile.assert_called_once()
    client.override_price_based_charging_profile.assert_not_called()


async def test_boost_without_smart_charging(hass: HomeAssistant, config_entry: MockConfigEntry, charge_point: dict[str, Any]) -> None:
    await init_integration(hass, config_entry, Platform.BUTTON, charge_point)
    state = hass.states.get(f"button.101_boost_charge_session")
    assert state
    assert state.state == STATE_UNAVAILABLE

async def test_boost_with_delayed_charging(hass: HomeAssistant, config_entry: MockConfigEntry, charge_point: dict[str, Any]) -> None:
    charge_point[SMART_CHARGING] = True
    charge_point[ACTIVITY] = DELAYED

    await init_integration(hass, config_entry, Platform.BUTTON, charge_point)
    state = hass.states.get(f"button.101_boost_charge_session")
    assert state
    assert state.state == STATE_UNKNOWN

async def test_boost_with_price_based_charging(hass: HomeAssistant, config_entry: MockConfigEntry, charge_point: dict[str, Any]) -> None:
    charge_point[SMART_CHARGING] = True
    charge_point[DELAYED_CHARGING][VALUE] = False
    charge_point[PRICE_BASED_CHARGING][VALUE] = True
    charge_point[ACTIVITY] = CHARGING

    await init_integration(hass, config_entry, Platform.BUTTON, charge_point)
    state = hass.states.get(f"button.101_boost_charge_session")
    assert state
    assert state.state == STATE_UNKNOWN
