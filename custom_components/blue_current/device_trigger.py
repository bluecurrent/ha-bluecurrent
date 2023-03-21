"""Provides device triggers for BlueCurrent."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components.device_automation import DEVICE_TRIGGER_BASE_SCHEMA
from homeassistant.components.homeassistant.triggers import state
from homeassistant.const import (
    CONF_DEVICE_ID,
    CONF_DOMAIN,
    CONF_ENTITY_ID,
    CONF_PLATFORM,
    CONF_TYPE,
)
from homeassistant.core import CALLBACK_TYPE, HomeAssistant
from homeassistant.helpers import config_validation as cv, device_registry
from homeassistant.helpers.trigger import TriggerActionType, TriggerInfo
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN

ACTIVITY_TYPES = {
    "available",
    "charging",
    "unavailable",
    "error",
    "offline",
}
VEHICLE_STATUS_TYPES = {
    "standby",
    "vehicle_detected",
    "ready",
    "no_power",
    "vehicle_error",
}

ACTIVITY_TRIGGER_SCHEMA = DEVICE_TRIGGER_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_TYPE): vol.In(ACTIVITY_TYPES),
        vol.Required(CONF_ENTITY_ID): cv.entity_id,
    }
)

VEHICLE_STATUS_TRIGGER_SCHEMA = DEVICE_TRIGGER_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_TYPE): vol.In(VEHICLE_STATUS_TYPES),
        vol.Required(CONF_ENTITY_ID): cv.entity_id,
    }
)

TRIGGER_SCHEMA = vol.Any(ACTIVITY_TRIGGER_SCHEMA, VEHICLE_STATUS_TRIGGER_SCHEMA)


async def async_get_triggers(
    hass: HomeAssistant, device_id: str
) -> list[dict[str, Any]]:
    """List device triggers for BlueCurrent devices."""
    triggers = []
    registry = device_registry.async_get(hass)
    device = registry.async_get(device_id)

    assert device is not None
    evse_id = list(device.identifiers)[0][1]

    base_trigger = {
        CONF_PLATFORM: "device",
        CONF_DEVICE_ID: device_id,
        CONF_DOMAIN: DOMAIN,
    }

    triggers.extend(
        [
            {
                **base_trigger,
                CONF_TYPE: t,
                CONF_ENTITY_ID: f"sensor.activity_{evse_id}",
            }
            for t in ACTIVITY_TYPES
        ]
    )

    triggers.extend(
        [
            {
                **base_trigger,
                CONF_TYPE: t,
                CONF_ENTITY_ID: f"sensor.vehicle_status_{evse_id}",
            }
            for t in VEHICLE_STATUS_TYPES
        ]
    )
    return triggers


async def async_attach_trigger(
    hass: HomeAssistant,
    config: ConfigType,
    action: TriggerActionType,
    trigger_info: TriggerInfo,
) -> CALLBACK_TYPE:
    """Attach a trigger."""
    state_config = {
        state.CONF_PLATFORM: "state",
        CONF_ENTITY_ID: config[CONF_ENTITY_ID],
        state.CONF_TO: config[CONF_TYPE],
    }

    state_config = await state.async_validate_trigger_config(hass, state_config)
    return await state.async_attach_trigger(
        hass, state_config, action, trigger_info, platform_type="device"
    )
