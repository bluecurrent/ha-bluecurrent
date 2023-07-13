"""Support for Blue Current buttons."""
from __future__ import annotations

from homeassistant.components.button import (
    ButtonEntity,
    ButtonEntityDescription,
    ButtonDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import Connector
from .const import DOMAIN, EVSE_ID
from .entity import BlueCurrentEntity

BUTTONS = (
    ButtonEntityDescription(
        key="reset",
        name="Reset",
        icon="mdi:restart",
        has_entity_name=True,
        device_class=ButtonDeviceClass.RESTART,
    ),
    ButtonEntityDescription(
        key="reboot",
        name="Reboot",
        icon="mdi:restart-alert",
        has_entity_name=True,
        device_class=ButtonDeviceClass.RESTART,
    ),
    ButtonEntityDescription(
        key="start_session", name="Start session", icon="mdi:play", has_entity_name=True
    ),
    ButtonEntityDescription(
        key="stop_session", name="Stop session", icon="mdi:stop", has_entity_name=True
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Blue Current buttons."""
    connector: Connector = hass.data[DOMAIN][entry.entry_id]
    button_list = []
    for evse_id in connector.charge_points:
        for button in BUTTONS:
            button_list.append(
                ChargePointButton(
                    connector,
                    evse_id,
                    button,
                )
            )

    async_add_entities(button_list)


class ChargePointButton(BlueCurrentEntity, ButtonEntity):
    """Base Blue Current button."""

    _attr_should_poll = False

    def __init__(
        self, connector: Connector, evse_id: str, button: ButtonEntityDescription
    ) -> None:
        """Initialize the button."""
        assert button.name is not None
        super().__init__(connector, evse_id)

        self.service = button.key
        self.entity_description = button
        self._attr_unique_id = f"{button.key}_{evse_id}"

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.hass.services.async_call(
            DOMAIN, self.service, {EVSE_ID: self.evse_id}
        )

    @callback
    def update_from_latest_data(self) -> None:
        """Fetch new state data for the button."""
