"""Provide the device conditions for BlueCurrent."""
from __future__ import annotations

import voluptuous as vol

from homeassistant.const import (
    ATTR_ENTITY_ID,
    CONF_CONDITION,
    CONF_DEVICE_ID,
    CONF_DOMAIN,
    CONF_ENTITY_ID,
    CONF_TYPE,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import condition, config_validation as cv, device_registry
from homeassistant.helpers.config_validation import DEVICE_CONDITION_BASE_SCHEMA
from homeassistant.helpers.typing import ConfigType, TemplateVarsType

from . import DOMAIN

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

ACTIVITY_CONDITION_SCHEMA = DEVICE_CONDITION_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_TYPE): vol.In(ACTIVITY_TYPES),
        vol.Required(CONF_ENTITY_ID): cv.entity_id,
    }
)

VEHICLE_STATUS_CONDITION_SCHEMA = DEVICE_CONDITION_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_TYPE): vol.In(VEHICLE_STATUS_TYPES),
        vol.Required(CONF_ENTITY_ID): cv.entity_id,
    }
)

CONDITION_SCHEMA = vol.Any(ACTIVITY_CONDITION_SCHEMA, VEHICLE_STATUS_CONDITION_SCHEMA)


async def async_get_conditions(
    hass: HomeAssistant, device_id: str
) -> list[dict[str, str]]:
    """List device conditions for BlueCurrent devices."""
    conditions = []
    registry = device_registry.async_get(hass)
    device = registry.async_get(device_id)

    assert device is not None
    evse_id = list(device.identifiers)[0][1]

    base_condition = {
        CONF_CONDITION: "device",
        CONF_DEVICE_ID: device_id,
        CONF_DOMAIN: DOMAIN,
    }

    conditions.extend(
        [
            {
                **base_condition,
                CONF_TYPE: t,
                CONF_ENTITY_ID: f"sensor.activity_{evse_id}",
            }
            for t in ACTIVITY_TYPES
        ]
    )

    conditions.extend(
        [
            {
                **base_condition,
                CONF_TYPE: t,
                CONF_ENTITY_ID: f"sensor.vehicle_status_{evse_id}",
            }
            for t in VEHICLE_STATUS_TYPES
        ]
    )
    return conditions


@callback
def async_condition_from_config(
    hass: HomeAssistant, config: ConfigType
) -> condition.ConditionCheckerType:
    """Create a function to test a device condition."""
    state = config[CONF_TYPE]

    @callback
    def test_is_state(hass: HomeAssistant, variables: TemplateVarsType) -> bool:
        """Test if an entity is a certain state."""
        return condition.state(hass, config[ATTR_ENTITY_ID], state)

    return test_is_state
