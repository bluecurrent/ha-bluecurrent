"""Support for Blue Current switches."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from bluecurrent_api import Client
from homeassistant.components.switch import (
    SwitchDeviceClass,
    SwitchEntity,
    SwitchEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import Connector
from .const import ACTIVITY, DOMAIN, LOGGER
from .entity import BlueCurrentEntity

AVAILABLE = "available"
BLOCK = 'block'

@dataclass
class BlueCurrentSwitchEntityDescriptionMixin:
    """Mixin for the called functions."""

    function: Callable[[Client, str, bool], Any]


@dataclass
class BlueCurrentSwitchEntityDescription(
    SwitchEntityDescription, BlueCurrentSwitchEntityDescriptionMixin
):
    """Describes Blue Current switch entity."""


SWITCHES: tuple[BlueCurrentSwitchEntityDescription, ...] = (
    BlueCurrentSwitchEntityDescription(
        key="plug_and_charge",
        device_class=SwitchDeviceClass.SWITCH,
        name="Plug and charge",
        icon="mdi:ev-plug-type2",
        function=lambda client, evse_id, value: client.set_plug_and_charge(
            evse_id, value
        ),
        has_entity_name=True,
    ),
    BlueCurrentSwitchEntityDescription(
        key="linked_charge_cards_only",
        device_class=SwitchDeviceClass.SWITCH,
        name="Linked charge cards only",
        icon="mdi:account-group",
        function=lambda client, evse_id, value: client.set_linked_charge_cards_only(
            evse_id, value
        ),
        has_entity_name=True,
    ),
    BlueCurrentSwitchEntityDescription(
        key="block",
        device_class=SwitchDeviceClass.SWITCH,
        name="Block",
        icon="mdi:lock",
        function=lambda client, evse_id, value: client.block(evse_id, value),
        has_entity_name=True,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Blue Current switches."""
    connector: Connector = hass.data[DOMAIN][entry.entry_id]

    switch_list = []
    for evse_id in connector.charge_points:
        for switch in SWITCHES:
            switch_list.append(
                ChargePointSwitch(
                    connector,
                    evse_id,
                    switch,
                )
            )

    async_add_entities(switch_list)


class ChargePointSwitch(BlueCurrentEntity, SwitchEntity):
    """Base charge point switch."""

    _attr_should_poll = False

    entity_description: BlueCurrentSwitchEntityDescription

    def __init__(
        self,
        connector: Connector,
        evse_id: str,
        switch: BlueCurrentSwitchEntityDescription,
    ) -> None:
        """Initialize the switch."""
        super().__init__(connector, evse_id)

        self.key = switch.key
        self.entity_description = switch
        self._attr_unique_id = f"{switch.key}_{evse_id}"

    async def call_function(self, value: bool) -> None:
        """Call the function to set setting."""
        try:
            await self.entity_description.function(
                self.connector.client, self.evse_id, value
            )
        except ConnectionError:
            LOGGER.error("No connection")

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        await self.call_function(True)
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        await self.call_function(False)
        self._attr_is_on = False
        self.async_write_ha_state()

    @callback
    def update_from_latest_data(self) -> None:
        """Fetch new state data for the switch."""
        new_value = self.connector.charge_points[self.evse_id].get(self.key)
        activity = self.connector.charge_points[self.evse_id].get(ACTIVITY)

        if new_value is not None and (activity == AVAILABLE or self.key == BLOCK):
            self._attr_is_on = new_value = new_value
            self._attr_available = True

        else:
            self._attr_available = False
