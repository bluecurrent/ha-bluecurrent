"""tests for Blue Current actions."""

from unittest.mock import call

from bluecurrent_api.types import OverrideCurrentPayload

from homeassistant.components.blue_current import DOMAIN
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from tests.common import MockConfigEntry
from . import DEFAULT_CHARGE_POINT, init_integration

SECOND_CHARGE_POINT = {
    "evse_id": "102",
    "model_type": "",
    "name": "",
}


async def test_user_override_with_new_schedule(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    """Test user override with a new schedule."""
    integration = await init_integration(
        hass,
        config_entry,
        Platform.BUTTON,
        charge_points=[DEFAULT_CHARGE_POINT, SECOND_CHARGE_POINT],
    )
    client = integration[0]

    await hass.services.async_call(
        DOMAIN,
        "set_user_override",
        {
            "device_ids": list(dr.async_get(hass).devices),
            "current": 10,
            "override_start_time": "10:00:00",
            "override_end_time": "20:00:00",
            "override_start_days": ["monday", "thursday"],
            "override_end_days": ["wednesday", "friday"],
        },
        blocking=True,
    )

    client.set_user_override_current.assert_called_once_with(
        OverrideCurrentPayload(
            chargepoints=["101", "102"],
            overridestarttime="10:00",
            overridestartdays=["MO", "TH"],
            overridestoptime="20:00",
            overridestopdays=["WE", "FR"],
            overridevalue=10,
        )
    )


async def test_user_override_with_existing_schedule(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    """Test user override with an already existing schedule."""
    schedules = [
        {
            "schedule_id": "TEST_ID",
            "charge_points": ["101", "102"],
            "override_current": 10,
            "start_time": "10:00",
            "stop_time": "20:00",
            "override_start_days": "MO,TH",
            "override_end_days": "WE,FR",
        }
    ]

    integration = await init_integration(
        hass,
        config_entry,
        Platform.BUTTON,
        schedules=schedules,
        charge_points=[DEFAULT_CHARGE_POINT, SECOND_CHARGE_POINT, SECOND_CHARGE_POINT],
    )
    client = integration[0]

    await hass.services.async_call(
        DOMAIN,
        "set_user_override",
        {
            "device_ids": [
                list(dr.async_get(hass).devices)[0],
                list(dr.async_get(hass).devices)[1],
            ],
            "current": 15,
            "override_start_time": "15:00",
            "override_end_time": "22:00",
            "override_start_days": ["saturday", "thursday"],
            "override_end_days": ["wednesday", "sunday"],
        },
        blocking=True,
    )

    client.edit_user_override_current.assert_called_once_with(
        "TEST_ID",
        OverrideCurrentPayload(
            chargepoints=["101", "102"],
            overridestarttime="15:00",
            overridestartdays=["SA", "TH"],
            overridestoptime="22:00",
            overridestopdays=["WE", "SU"],
            overridevalue=15,
        ),
    )


async def test_user_override_with_different_schedule(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    """Test user override with different schedules for the charging points."""
    schedules = [
        {
            "schedule_id": "TEST_ID",
            "charge_points": ["101"],
            "override_current": 10,
            "start_time": "10:00",
            "stop_time": "20:00",
            "override_start_days": "MO,TH",
            "override_end_days": "WE,FR",
        },
        {
            "schedule_id": "TEST_ID_1",
            "charge_points": ["102"],
            "override_current": 10,
            "start_time": "10:00",
            "stop_time": "20:00",
            "override_start_days": "MO,TH",
            "override_end_days": "WE,FR",
        },
    ]

    integration = await init_integration(
        hass,
        config_entry,
        Platform.BUTTON,
        schedules=schedules,
        charge_points=[DEFAULT_CHARGE_POINT, SECOND_CHARGE_POINT, SECOND_CHARGE_POINT],
    )
    client = integration[0]

    await hass.services.async_call(
        DOMAIN,
        "set_user_override",
        {
            "device_ids": [
                list(dr.async_get(hass).devices)[0],
                list(dr.async_get(hass).devices)[1],
            ],
            "current": 15,
            "override_start_time": "15:00:00",
            "override_end_time": "22:00:00",
            "override_start_days": ["saturday", "thursday"],
            "override_end_days": ["wednesday", "sunday"],
        },
        blocking=True,
    )

    client.set_user_override_current.assert_called_once_with(
        OverrideCurrentPayload(
            chargepoints=["101", "102"],
            overridestarttime="15:00",
            overridestartdays=["SA", "TH"],
            overridestoptime="22:00",
            overridestopdays=["WE", "SU"],
            overridevalue=15,
        )
    )

    assert call("TEST_ID") in client.clear_user_override_current.call_args_list
    assert call("TEST_ID_1") in client.clear_user_override_current.call_args_list


async def test_user_override_without_all_chargepoints(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    """Test user override when a schedule needs to be updated but not all schedule charge points are given."""
    schedules = [
        {
            "schedule_id": "TEST_ID",
            "charge_points": ["101", "102"],
            "override_current": 10,
            "start_time": "10:00",
            "stop_time": "20:00",
            "override_start_days": ["MO", "TH"],
            "override_end_days": ["WE", "FR"],
        },
    ]

    integration = await init_integration(
        hass,
        config_entry,
        Platform.BUTTON,
        schedules=schedules,
        charge_points=[DEFAULT_CHARGE_POINT, SECOND_CHARGE_POINT, SECOND_CHARGE_POINT],
    )
    client = integration[0]

    await hass.services.async_call(
        DOMAIN,
        "set_user_override",
        {
            "device_ids": [
                list(dr.async_get(hass).devices)[0],
            ],
            "current": 15,
            "override_start_time": "15:00:00",
            "override_end_time": "22:00:00",
            "override_start_days": ["saturday", "thursday"],
            "override_end_days": ["wednesday", "sunday"],
        },
        blocking=True,
    )

    client.set_user_override_current.assert_called_once_with(
        OverrideCurrentPayload(
            chargepoints=["101"],
            overridestarttime="15:00",
            overridestartdays=["SA", "TH"],
            overridestoptime="22:00",
            overridestopdays=["WE", "SU"],
            overridevalue=15,
        )
    )

    assert (
        call(
            "TEST_ID",
            OverrideCurrentPayload(
                chargepoints=["102"],
                overridestarttime="10:00",
                overridestartdays=["MO", "TH"],
                overridestoptime="20:00",
                overridestopdays=["WE", "FR"],
                overridevalue=10,
            ),
        )
        in client.edit_user_override_current.call_args_list
    )


async def test_user_override_with_other_chargepoints(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    """Test user override with different change points in the schedule."""
    schedules = [
        {
            "schedule_id": "TEST_ID",
            "charge_points": ["101", "103"],
            "override_current": 10,
            "start_time": "10:00",
            "stop_time": "15:00",
            "override_start_days": ["MO", "TH"],
            "override_end_days": ["WE", "FR"],
        },
        {
            "schedule_id": "TEST_ID_1",
            "charge_points": ["102", "104"],
            "override_current": 10,
            "start_time": "10:00",
            "stop_time": "20:00",
            "override_start_days": ["MO", "TH"],
            "override_end_days": ["WE", "FR"],
        },
    ]

    integration = await init_integration(
        hass,
        config_entry,
        Platform.BUTTON,
        schedules=schedules,
        charge_points=[DEFAULT_CHARGE_POINT, SECOND_CHARGE_POINT],
    )
    client = integration[0]

    await hass.services.async_call(
        DOMAIN,
        "set_user_override",
        {
            "device_ids": [
                list(dr.async_get(hass).devices)[0],
                list(dr.async_get(hass).devices)[1],
            ],
            "current": 15,
            "override_start_time": "15:00:00",
            "override_end_time": "22:00:00",
            "override_start_days": ["saturday", "thursday"],
            "override_end_days": ["wednesday", "sunday"],
        },
        blocking=True,
    )

    client.set_user_override_current.assert_called_once_with(
        OverrideCurrentPayload(
            chargepoints=["101", "102"],
            overridestarttime="15:00",
            overridestartdays=["SA", "TH"],
            overridestoptime="22:00",
            overridestopdays=["WE", "SU"],
            overridevalue=15,
        )
    )

    assert (
        call(
            "TEST_ID",
            OverrideCurrentPayload(
                chargepoints=["103"],
                overridestarttime="10:00",
                overridestartdays=["MO", "TH"],
                overridestoptime="15:00",
                overridestopdays=["WE", "FR"],
                overridevalue=10,
            ),
        )
        in client.edit_user_override_current.call_args_list
    )

    assert (
        call(
            "TEST_ID_1",
            OverrideCurrentPayload(
                chargepoints=["104"],
                overridestarttime="10:00",
                overridestartdays=["MO", "TH"],
                overridestoptime="20:00",
                overridestopdays=["WE", "FR"],
                overridevalue=10,
            ),
        )
        in client.edit_user_override_current.call_args_list
    )


async def test_clear_user_override(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    """Test user override with different change points in the schedule."""
    schedules = [
        {
            "schedule_id": "TEST_ID",
            "charge_points": ["101"],
            "override_current": 10,
            "start_time": "10:00",
            "stop_time": "15:00",
            "override_start_days": ["MO", "TH"],
            "override_end_days": ["WE", "FR"],
        }
    ]

    integration = await init_integration(
        hass,
        config_entry,
        Platform.BUTTON,
        schedules=schedules,
        charge_points=[DEFAULT_CHARGE_POINT, SECOND_CHARGE_POINT],
    )
    client = integration[0]

    await hass.services.async_call(
        DOMAIN,
        "clear_user_override",
        {"device_ids": [list(dr.async_get(hass).devices)[0]]},
        blocking=True,
    )

    assert call("TEST_ID") in client.clear_user_override_current.call_args_list
    assert client.edit_user_override_current.call_count == 0
    assert client.set_user_override_current.call_count == 0


async def test_clear_user_override_without_all_charge_points(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    """Test user override with different change points in the schedule."""
    schedules = [
        {
            "schedule_id": "TEST_ID",
            "charge_points": ["101", "103"],
            "override_current": 10,
            "start_time": "10:00",
            "stop_time": "15:00",
            "override_start_days": ["MO", "TH"],
            "override_end_days": ["WE", "FR"],
        }
    ]

    integration = await init_integration(
        hass,
        config_entry,
        Platform.BUTTON,
        schedules=schedules,
        charge_points=[DEFAULT_CHARGE_POINT, SECOND_CHARGE_POINT],
    )
    client = integration[0]

    await hass.services.async_call(
        DOMAIN,
        "clear_user_override",
        {"device_ids": [list(dr.async_get(hass).devices)[0]]},
        blocking=True,
    )

    assert (
        call(
            "TEST_ID",
            OverrideCurrentPayload(
                chargepoints=["103"],
                overridestarttime="10:00",
                overridestartdays=["MO", "TH"],
                overridestoptime="15:00",
                overridestopdays=["WE", "FR"],
                overridevalue=10,
            ),
        )
        in client.edit_user_override_current.call_args_list
    )

    assert client.set_user_override_current.call_count == 0
    assert client.clear_user_override_current.call_count == 0
