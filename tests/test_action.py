"""tests for Blue Current actions."""
from unittest.mock import call

import pytest
from bluecurrent_api.types import OverrideCurrentPayload

from homeassistant.components.blue_current import DOMAIN
from homeassistant.components.blue_current.const import (
    DELAYED_CHARGING,
    PRICE_BASED_CHARGING,
    SMART_CHARGING,
    VALUE,
)
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import device_registry as dr

from . import DEFAULT_CHARGE_POINT, init_integration

from tests.common import MockConfigEntry


async def test_price_based_charging_action(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    """Test the set price based charging action."""
    charge_point = DEFAULT_CHARGE_POINT.copy()
    charge_point[SMART_CHARGING] = True
    charge_point[PRICE_BASED_CHARGING] = {VALUE: True}
    charge_point[DELAYED_CHARGING] = {VALUE: False}

    integration = await init_integration(
        hass, config_entry, Platform.BUTTON, charge_point
    )
    client = integration[0]

    await hass.services.async_call(
        DOMAIN,
        "set_price_based_charging",
        {
            "device_id": list(dr.async_get(hass).devices)[0],
            "expected_departure_time": "20:00:00",
            "expected_charging_session_size": 20,
            "immediately_charge": 10,
        },
        blocking=True,
    )

    client.set_price_based_settings.assert_called_once_with("101", "20:00", 20, 10)

    await hass.services.async_call(
        DOMAIN,
        "set_price_based_charging",
        {
            "device_id": list(dr.async_get(hass).devices)[0],
            "expected_departure_time": "20:00",
            "expected_charging_session_size": 20,
            "immediately_charge": 10,
        },
        blocking=True,
    )

    client.set_price_based_settings.assert_called_with("101", "20:00", 20, 10)


async def test_price_based_charging_action_errors_session_size(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    """Test the set price based charging action charge size errors."""
    charge_point = DEFAULT_CHARGE_POINT.copy()
    charge_point[SMART_CHARGING] = True
    charge_point[PRICE_BASED_CHARGING] = {VALUE: True}
    charge_point[DELAYED_CHARGING] = {VALUE: False}

    await init_integration(hass, config_entry, Platform.BUTTON, charge_point)

    with pytest.raises(ServiceValidationError):
        # Session size too small expected charging session size.
        await hass.services.async_call(
            DOMAIN,
            "set_price_based_charging",
            {
                "device_id": list(dr.async_get(hass).devices)[0],
                "expected_departure_time": "20:00:00",
                "expected_charging_session_size": 0,
                "immediately_charge": 10,
            },
            blocking=True,
        )

    with pytest.raises(ServiceValidationError):
        # Session size too small expected session size
        await hass.services.async_call(
            DOMAIN,
            "set_price_based_charging",
            {
                "device_id": list(dr.async_get(hass).devices)[0],
                "expected_departure_time": "20:00:00",
                "expected_charging_session_size": 10,
                "immediately_charge": 0,
            },
            blocking=True,
        )

    with pytest.raises(ServiceValidationError):
        # Session size too big expected charging session size.
        await hass.services.async_call(
            DOMAIN,
            "set_price_based_charging",
            {
                "device_id": list(dr.async_get(hass).devices)[0],
                "expected_departure_time": "20:00:00",
                "expected_charging_session_size": 81,
                "immediately_charge": 10,
            },
            blocking=True,
        )

    with pytest.raises(ServiceValidationError):
        # Session size too small immediately charge
        await hass.services.async_call(
            DOMAIN,
            "set_price_based_charging",
            {
                "device_id": list(dr.async_get(hass).devices)[0],
                "expected_departure_time": "20:00:00",
                "expected_charging_session_size": 10,
                "immediately_charge": 81,
            },
            blocking=True,
        )


async def test_price_based_charging_action_errors_time(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    """Test the set price based charging action charge time errors."""
    charge_point = DEFAULT_CHARGE_POINT.copy()
    charge_point[SMART_CHARGING] = True
    charge_point[PRICE_BASED_CHARGING] = {VALUE: True}
    charge_point[DELAYED_CHARGING] = {VALUE: False}

    await init_integration(hass, config_entry, Platform.BUTTON, charge_point)

    with pytest.raises(ServiceValidationError):
        # Expected time does not contain a timestamp.
        await hass.services.async_call(
            DOMAIN,
            "set_price_based_charging",
            {
                "device_id": list(dr.async_get(hass).devices)[0],
                "expected_departure_time": "INVALID_TIME",
                "expected_charging_session_size": 0,
                "immediately_charge": 10,
            },
            blocking=True,
        )

    with pytest.raises(ServiceValidationError):
        # Expected time does not contain a valid timestamp.
        await hass.services.async_call(
            DOMAIN,
            "set_price_based_charging",
            {
                "device_id": list(dr.async_get(hass).devices)[0],
                "expected_departure_time": "21:99:99",
                "expected_charging_session_size": 0,
                "immediately_charge": 10,
            },
            blocking=True,
        )


async def test_set_delayed_charging_action(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    """Test the set delayed charging action."""
    charge_point = DEFAULT_CHARGE_POINT.copy()
    charge_point[SMART_CHARGING] = True
    charge_point[PRICE_BASED_CHARGING] = {VALUE: False}
    charge_point[DELAYED_CHARGING] = {VALUE: True}

    integration = await init_integration(
        hass, config_entry, Platform.BUTTON, charge_point
    )
    client = integration[0]

    await hass.services.async_call(
        DOMAIN,
        "set_delayed_charging",
        {
            "device_id": list(dr.async_get(hass).devices)[0],
            "end_time": "10:00:00",
            "start_time": "20:00:00",
            "days": ["monday", "thursday"],
        },
        blocking=True,
    )
    # 1: monday, 4: thursday
    client.save_scheduled_delayed_charging.assert_called_once_with(
        "101", [1, 4], "20:00", "10:00"
    )

    await hass.services.async_call(
        DOMAIN,
        "set_delayed_charging",
        {
            "device_id": list(dr.async_get(hass).devices)[0],
            "end_time": "10:00",
            "start_time": "20:00",
            "days": ["monday", "thursday"],
        },
        blocking=True,
    )
    # 1: monday, 4: thursday
    client.save_scheduled_delayed_charging.assert_called_with(
        "101", [1, 4], "20:00", "10:00"
    )


async def test_delayed_charging_action_errors_time(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    """Test the set delayed charging action time errors."""
    charge_point = DEFAULT_CHARGE_POINT.copy()
    charge_point[SMART_CHARGING] = True
    charge_point[PRICE_BASED_CHARGING] = {VALUE: False}
    charge_point[DELAYED_CHARGING] = {VALUE: True}

    await init_integration(hass, config_entry, Platform.BUTTON, charge_point)

    with pytest.raises(ServiceValidationError):
        # Expected time does not contain a timestamp for end_time.
        await hass.services.async_call(
            DOMAIN,
            "set_delayed_charging",
            {
                "device_id": list(dr.async_get(hass).devices)[0],
                "end_time": "INVALID_TIME",
                "start_time": "20:00:00",
                "days": ["monday", "thursday"],
            },
            blocking=True,
        )

    with pytest.raises(ServiceValidationError):
        # Expected time does not contain a timestamp for end_time.
        await hass.services.async_call(
            DOMAIN,
            "set_delayed_charging",
            {
                "device_id": list(dr.async_get(hass).devices)[0],
                "end_time": "10:00:00",
                "start_time": "INVALID_TIME",
                "days": ["monday", "thursday"],
            },
            blocking=True,
        )

    with pytest.raises(ServiceValidationError):
        # Expected time does not contain a timestamp for end_time.
        await hass.services.async_call(
            DOMAIN,
            "set_delayed_charging",
            {
                "device_id": list(dr.async_get(hass).devices)[0],
                "end_time": "19:99:99",
                "start_time": "10:00:00",
                "days": ["monday", "thursday"],
            },
            blocking=True,
        )

    with pytest.raises(ServiceValidationError):
        # Expected time does not contain a timestamp for end_time.
        await hass.services.async_call(
            DOMAIN,
            "set_delayed_charging",
            {
                "device_id": list(dr.async_get(hass).devices)[0],
                "end_time": "12:00:00",
                "start_time": "19:99:99",
                "days": ["monday", "thursday"],
            },
            blocking=True,
        )


async def test_switch_profile_action_with_no_selected_profile(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    """Test the switch profile action when no other profile has been selected."""
    charge_point = DEFAULT_CHARGE_POINT.copy()
    charge_point[SMART_CHARGING] = True
    charge_point[PRICE_BASED_CHARGING] = {VALUE: False}
    charge_point[DELAYED_CHARGING] = {VALUE: False}

    integration = await init_integration(
        hass, config_entry, Platform.BUTTON, charge_point
    )
    client = integration[0]

    await hass.services.async_call(
        DOMAIN,
        "set_price_based_charging",
        {
            "device_id": list(dr.async_get(hass).devices)[0],
            "expected_departure_time": "20:00:00",
            "expected_charging_session_size": 20,
            "immediately_charge": 10,
        },
        blocking=True,
    )

    client.set_price_based_charging.assert_called_once_with("101", True)


async def test_switch_profile_action_with_previous_selected_profile(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    """Test the switch profile action when another profile has been selected already."""
    charge_point = DEFAULT_CHARGE_POINT.copy()
    charge_point[SMART_CHARGING] = True
    charge_point[PRICE_BASED_CHARGING] = {VALUE: True}
    charge_point[DELAYED_CHARGING] = {VALUE: False}

    integration = await init_integration(
        hass, config_entry, Platform.BUTTON, charge_point
    )
    client = integration[0]

    await hass.services.async_call(
        DOMAIN,
        "set_delayed_charging",
        {
            "device_id": list(dr.async_get(hass).devices)[0],
            "end_time": "10:00:00",
            "start_time": "20:00:00",
            "days": ["monday", "thursday"],
        },
        blocking=True,
    )

    client.set_price_based_charging.assert_called_once_with("101", False)
    client.set_delayed_charging.assert_called_once_with("101", True)

async def test_user_override_with_new_schedule(hass: HomeAssistant, config_entry: MockConfigEntry):
    """Test user override with a new schedule."""
    integration = await init_integration(hass, config_entry, Platform.BUTTON)
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

    client.set_user_override_current.assert_called_once_with(OverrideCurrentPayload(
            chargepoints=["101", "102"],
            overridestarttime="10:00",
            overridestartdays=["MO", "TH"],
            overridestoptime="20:00",
            overridestopdays=["WE", "FR"],
            overridevalue=10,
        ))

async def test_user_override_with_existing_schedule(hass: HomeAssistant, config_entry: MockConfigEntry):
    """Test user override with an already existing schedule."""
    schedules = [
        {
            "schedule_id": "TEST_ID",
            "charge_points": ["101", "102"],
            "current": 10,
            "override_start_time": "10:00",
            "override_end_time": "20:00",
            "override_start_days": ["monday", "thursday"],
            "override_end_days": ["wednesday", "friday"],
        }
    ]

    integration = await init_integration(hass, config_entry, Platform.BUTTON, schedules=schedules)
    client = integration[0]

    await hass.services.async_call(
        DOMAIN,
        "set_user_override",
        {
            "device_ids": [list(dr.async_get(hass).devices)[0], list(dr.async_get(hass).devices)[1]],
            "current": 15,
            "override_start_time": "15:00",
            "override_end_time": "22:00",
            "override_start_days": ["saturday", "thursday"],
            "override_end_days": ["wednesday", "sunday"],
        },
        blocking=True,
    )

    client.edit_user_override_current.assert_called_once_with("TEST_ID", OverrideCurrentPayload(
            chargepoints=["101", "102"],
            overridestarttime="15:00",
            overridestartdays=["SA", "TH"],
            overridestoptime="22:00",
            overridestopdays=["WE", "SU"],
            overridevalue=15,
        ))

async def test_user_override_with_different_schedule(hass: HomeAssistant, config_entry: MockConfigEntry):
    """Test user override with different schedules for the charging points."""
    schedules = [
        {
            "schedule_id": "TEST_ID",
            "charge_points": ["101"],
            "current": 10,
            "override_start_time": "10:00",
            "override_end_time": "20:00",
            "override_start_days": ["monday", "thursday"],
            "override_end_days": ["wednesday", "friday"],
        },
    {
            "schedule_id": "TEST_ID_1",
            "charge_points": ["102"],
            "current": 10,
            "override_start_time": "10:00",
            "override_end_time": "20:00",
            "override_start_days": ["monday", "thursday"],
            "override_end_days": ["wednesday", "friday"],
        }
    ]

    integration = await init_integration(hass, config_entry, Platform.BUTTON, schedules=schedules)
    client = integration[0]

    await hass.services.async_call(
        DOMAIN,
        "set_user_override",
        {
            "device_ids": [list(dr.async_get(hass).devices)[0], list(dr.async_get(hass).devices)[1]],
            "current": 15,
            "override_start_time": "15:00:00",
            "override_end_time": "22:00:00",
            "override_start_days": ["saturday", "thursday"],
            "override_end_days": ["wednesday", "sunday"],
        },
        blocking=True,
    )

    client.set_user_override_current.assert_called_once_with(OverrideCurrentPayload(
            chargepoints=["101", "102"],
            overridestarttime="15:00",
            overridestartdays=["SA", "TH"],
            overridestoptime="22:00",
            overridestopdays=["WE", "SU"],
            overridevalue=15,
        ))

    assert call("TEST_ID") in client.clear_user_override_current.call_args_list
    assert call("TEST_ID_1") in client.clear_user_override_current.call_args_list

async def test_user_override_with_other_chargepoints(hass: HomeAssistant, config_entry: MockConfigEntry):
    """Test user override with different change points in the schedule."""
    schedules = [
        {
            "schedule_id": "TEST_ID",
            "charge_points": ["101", "103"],
            "current": 10,
            "override_start_time": "10:00",
            "override_end_time": "15:00",
            "override_start_days": ["monday", "thursday"],
            "override_end_days": ["wednesday", "friday"],
        },
    {
            "schedule_id": "TEST_ID_1",
            "charge_points": ["102", "104"],
            "current": 10,
            "override_start_time": "10:00",
            "override_end_time": "20:00",
            "override_start_days": ["monday", "thursday"],
            "override_end_days": ["wednesday", "friday"],
        }
    ]

    integration = await init_integration(hass, config_entry, Platform.BUTTON, schedules=schedules)
    client = integration[0]

    await hass.services.async_call(
        DOMAIN,
        "set_user_override",
        {
            "device_ids": [list(dr.async_get(hass).devices)[0], list(dr.async_get(hass).devices)[1]],
            "current": 15,
            "override_start_time": "15:00:00",
            "override_end_time": "22:00:00",
            "override_start_days": ["saturday", "thursday"],
            "override_end_days": ["wednesday", "sunday"],
        },
        blocking=True,
    )

    client.set_user_override_current.assert_called_once_with(OverrideCurrentPayload(
            chargepoints=["101", "102"],
            overridestarttime="15:00",
            overridestartdays=["SA", "TH"],
            overridestoptime="22:00",
            overridestopdays=["WE", "SU"],
            overridevalue=15,
        ))

    print(client.edit_user_override_current.call_args_list)

    assert call("TEST_ID", OverrideCurrentPayload(
            chargepoints=["103"],
            overridestarttime="10:00",
            overridestartdays=["MO", "TH"],
            overridestoptime="15:00",
            overridestopdays=["WE", "FR"],
            overridevalue=10,
        )) in client.edit_user_override_current.call_args_list

    assert call("TEST_ID_1", OverrideCurrentPayload(
        chargepoints=["104"],
        overridestarttime="10:00",
        overridestartdays=["MO", "TH"],
        overridestoptime="20:00",
        overridestopdays=["WE", "FR"],
        overridevalue=10,
    )) in client.edit_user_override_current.call_args_list
