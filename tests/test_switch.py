"""The tests for Bluecurrent switches."""
import asyncio
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.dispatcher import async_dispatcher_send

from custom_components.blue_current import Connector

from . import init_integration

charge_point: dict[str, bool] = {
    "plug_and_charge": True,
    "linked_charge_cards_only": False,
}

data: dict[str, Any] = {
    "101": {
        "model_type": "hidden",
        "evse_id": "101",
        "name": "",
        "activity": "available",
        **charge_point,
    }
}


async def test_switches(hass: HomeAssistant):
    """Test the underlying switches."""

    await init_integration(hass, "switch", data)

    entity_registry = er.async_get(hass)
    for key, value in charge_point.items():
        state = hass.states.get(f"switch.101_{key}")

        if value:
            check = "on"
        else:
            check = "off"
        assert state and state.state == check
        entry = entity_registry.async_get(f"switch.101_{key}")
        assert entry and entry.unique_id == f"{key}_101"

    # block
    switches = er.async_entries_for_config_entry(entity_registry, "uuid")
    assert len(charge_point.keys()) == len(switches) - 1

    state = hass.states.get("switch.101_block")
    assert state and state.state == "unavailable"
    entry = entity_registry.async_get("switch.101_block")
    assert entry and entry.unique_id == "block_101"


async def test_toggle(hass: HomeAssistant):
    """Test the on / off methods and if the switch gets updated."""

    await init_integration(hass, "switch", data)

    state = hass.states.get("switch.101_linked_charge_cards_only")

    assert state and state.state == "off"
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": "switch.101_linked_charge_cards_only"},
        blocking=True,
    )

    connector: Connector = hass.data["blue_current"]["uuid"]
    connector.charge_points = {
        "101": {"activity": "available", "linked_charge_cards_only": True}
    }
    async_dispatcher_send(hass, "blue_current_value_update_101")

    # wait
    await asyncio.sleep(1)

    state = hass.states.get("switch.101_linked_charge_cards_only")
    assert state and state.state == "on"

    await hass.services.async_call(
        "switch",
        "turn_off",
        {"entity_id": "switch.101_linked_charge_cards_only"},
        blocking=True,
    )

    connector.charge_points = {
        "101": {"activity": "available", "linked_charge_cards_only": False}
    }
    async_dispatcher_send(hass, "blue_current_value_update_101")

    # wait
    await asyncio.sleep(1)

    state = hass.states.get("switch.101_linked_charge_cards_only")
    assert state and state.state == "off"

    connector.charge_points = {
        "101": {
            "activity": "charging",
            "linked_charge_cards_only": False,
            "block": False,
        }
    }
    async_dispatcher_send(hass, "blue_current_value_update_101")

    # wait
    await asyncio.sleep(1)

    state = hass.states.get("switch.101_linked_charge_cards_only")
    assert state and state.state == "unavailable"

    state = hass.states.get("switch.101_block")
    assert state and state.state == "off"
