"""Test Blue Current Init Component."""

from datetime import timedelta
from typing import Any
from unittest.mock import patch

from bluecurrent_api.client import Client
from bluecurrent_api.exceptions import RequestLimitReached, WebsocketException
import pytest

from homeassistant.components.blue_current import (
    DOMAIN,
    Connector,
    async_setup_entry,
    set_entities_unavalible,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from . import init_integration

from tests.common import MockConfigEntry


async def test_load_unload_entry(hass: HomeAssistant):
    """Test load and unload entry."""
    config_entry = await init_integration(hass, "sensor", {})
    assert config_entry.state == ConfigEntryState.LOADED
    assert isinstance(hass.data[DOMAIN][config_entry.entry_id], Connector)

    await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()
    assert config_entry.state == ConfigEntryState.NOT_LOADED
    assert hass.data[DOMAIN] == {}


async def test_config_not_ready(hass: HomeAssistant):
    """Tests if ConfigEntryNotReady is raised when connect raises a WebsocketException."""
    with patch(
        "bluecurrent_api.Client.connect",
        side_effect=WebsocketException,
    ), pytest.raises(ConfigEntryNotReady):
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            entry_id="uuid",
            unique_id="uuid",
            data={"api_token": "123", "card": {"123"}},
        )
        config_entry.add_to_hass(hass)

        await async_setup_entry(hass, config_entry)


async def test_set_entities_unavalible(hass: HomeAssistant):
    """Tests set_entities_unavailable."""

    data = {
        "101": {
            "model_type": "hidden",
            "evse_id": "101",
        }
    }

    charge_point = {
        "actual_v1": 14,
        "actual_v2": 18,
        "actual_v3": 15,
        "actual_p1": 19,
        "actual_p2": 14,
        "actual_p3": 15,
    }

    entity_ids = [
        "voltage_phase_1",
        "voltage_phase_2",
        "voltage_phase_3",
        "current_phase_1",
        "current_phase_2",
        "current_phase_3",
    ]

    await init_integration(hass, "sensor", data, charge_point)

    set_entities_unavalible(hass, "uuid")

    for entity_id in entity_ids:
        state = hass.states.get(f"sensor.101_{entity_id}")
        assert state
        assert state.state == "unavailable"


async def test_on_data(hass: HomeAssistant):
    """Test on_data."""

    await init_integration(hass, "sensor", {})

    with patch(
        "homeassistant.components.blue_current.async_dispatcher_send"
    ) as test_async_dispatcher_send:

        connector: Connector = hass.data[DOMAIN]["uuid"]

        # test CHARGE_POINTS
        data = {
            "object": "CHARGE_POINTS",
            "data": [{"evse_id": "101", "model_type": "hidden"}],
        }
        await connector.on_data(data)
        assert connector.charge_points == {"101": {"model_type": "hidden"}}

        # test CH_STATUS
        data2 = {
            "object": "CH_STATUS",
            "data": {
                "actual_v1": 12,
                "actual_v2": 14,
                "actual_v3": 15,
                "actual_p1": 12,
                "actual_p2": 14,
                "actual_p3": 15,
                "activity": "charging",
                "start_datetime": "2021-11-18T14:12:23",
                "stop_datetime": "2021-11-18T14:32:23",
                "offline_since": "2021-11-18T14:32:23",
                "total_cost": 10.52,
                "vehicle_status": "standby",
                "actual_kwh": 10,
                "evse_id": "101",
            },
        }
        await connector.on_data(data2)
        assert connector.charge_points == {
            "101": {
                "model_type": "hidden",
                "actual_v1": 12,
                "actual_v2": 14,
                "actual_v3": 15,
                "actual_p1": 12,
                "actual_p2": 14,
                "actual_p3": 15,
                "operative": True,
                "activity": "charging",
                "start_datetime": "2021-11-18T14:12:23",
                "stop_datetime": "2021-11-18T14:32:23",
                "offline_since": "2021-11-18T14:32:23",
                "total_cost": 10.52,
                "vehicle_status": "standby",
                "actual_kwh": 10,
            }
        }

        test_async_dispatcher_send.assert_called_with(
            hass, "blue_current_value_update_101"
        )

        # test GRID_STATUS
        data3 = {
            "object": "GRID_STATUS",
            "data": {
                "grid_actual_p1": 12,
                "grid_actual_p2": 14,
                "grid_actual_p3": 15,
            },
        }
        await connector.on_data(data3)
        assert connector.grid == {
            "grid_actual_p1": 12,
            "grid_actual_p2": 14,
            "grid_actual_p3": 15,
        }
        test_async_dispatcher_send.assert_called_with(hass, "blue_current_grid_update")

        # reset charge_point
        connector.charge_points["101"] = {}

        # test CH_SETTINGS
        data4: dict[str, Any] = {
            "object": "CH_SETTINGS",
            "data": {
                "plug_and_charge": False,
                "public_charging": False,
                "evse_id": "101",
            },
        }
        await connector.on_data(data4)
        assert connector.charge_points == {
            "101": {
                "plug_and_charge": False,
                "public_charging": False,
            }
        }
        test_async_dispatcher_send.assert_called_with(
            hass, "blue_current_value_update_101"
        )

        # test PUBLIC_CHARGING
        data5: dict[str, Any] = {
            "object": "PUBLIC_CHARGING",
            "result": True,
            "evse_id": "101",
        }
        await connector.on_data(data5)
        assert connector.charge_points == {
            "101": {
                "plug_and_charge": False,
                "public_charging": True,
            }
        }
        test_async_dispatcher_send.assert_called_with(
            hass, "blue_current_value_update_101"
        )

        # test PLUG_AND_CHARGE
        data7: dict[str, Any] = {
            "object": "PLUG_AND_CHARGE",
            "result": True,
            "evse_id": "101",
        }
        await connector.on_data(data7)
        assert connector.charge_points == {
            "101": {
                "plug_and_charge": True,
                "public_charging": True,
            }
        }
        test_async_dispatcher_send.assert_called_with(
            hass, "blue_current_value_update_101"
        )

        # test SOFT_RESET
        data7 = {"object": "STATUS_SOFT_RESET", "success": True}
        await connector.on_data(data7)

        # test REBOOT
        data8 = {"object": "STATUS_REBOOT", "success": False}
        await connector.on_data(data8)


async def test_start_loop(hass: HomeAssistant):
    """Tests start_loop."""

    with patch(
        "homeassistant.components.blue_current.async_call_later"
    ) as test_async_call_later:

        config_entry = MockConfigEntry(
            domain=DOMAIN,
            entry_id="uuid",
            unique_id="uuid",
            data={"api_token": "123", "card": {"123"}},
        )

        connector = Connector(hass, config_entry, Client)

        with patch(
            "bluecurrent_api.Client.start_loop",
            side_effect=WebsocketException("unknown command"),
        ):
            await connector.start_loop()
            test_async_call_later.assert_called_with(hass, 1, connector.reconnect)

        with patch(
            "bluecurrent_api.Client.start_loop", side_effect=RequestLimitReached
        ):
            await connector.start_loop()
            test_async_call_later.assert_called_with(hass, 1, connector.reconnect)


async def test_reconnect(hass: HomeAssistant):
    """Tests reconnect."""

    with patch("bluecurrent_api.Client.connect"), patch(
        "bluecurrent_api.Client.connect", side_effect=WebsocketException
    ), patch(
        "bluecurrent_api.Client.get_next_reset_delta", return_value=timedelta(hours=1)
    ), patch(
        "homeassistant.components.blue_current.async_call_later"
    ) as test_async_call_later:

        config_entry = MockConfigEntry(
            domain=DOMAIN,
            entry_id="uuid",
            unique_id="uuid",
            data={"api_token": "123", "card": {"123"}},
        )

        connector = Connector(hass, config_entry, Client)
        await connector.reconnect()

        test_async_call_later.assert_called_with(hass, 20, connector.reconnect)

        with patch("bluecurrent_api.Client.connect", side_effect=RequestLimitReached):
            await connector.reconnect()
            test_async_call_later.assert_called_with(
                hass, timedelta(hours=1), connector.reconnect
            )
