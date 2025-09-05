"""Support for Blue Current buttons."""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any

from bluecurrent_api.client import Client

from homeassistant.components.button import (
    ButtonDeviceClass,
    ButtonEntity,
    ButtonEntityDescription,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import EVSE_ID, BlueCurrentConfigEntry, Connector
from .const import (
    ACTIVITY,
    CHARGING,
    DELAYED,
    DELAYED_CHARGING,
    PRICE_BASED_CHARGING,
    SMART_CHARGING,
    VALUE,
    VEHICLE_ERROR,
    VEHICLE_STATUS,
)
from .entity import ChargepointEntity


@dataclass(kw_only=True, frozen=True)
class ChargePointButtonEntityDescription(ButtonEntityDescription):
    """Describes a Blue Current button entity."""

    function: Callable[[Client, dict[str, Any]], Coroutine[Any, Any, None]]
    is_button_available: Callable[[dict[str, Any]], bool] | None = None


async def boost_charge_session(client: Client, charge_point: dict[str, Any]) -> None:
    """Override the smart charging profile, if active."""
    if charge_point[SMART_CHARGING]:
        if charge_point[PRICE_BASED_CHARGING][VALUE]:
            await client.override_price_based_charging_profile(
                charge_point[EVSE_ID], True
            )
        if charge_point[DELAYED_CHARGING][VALUE]:
            await client.override_delayed_charging_profile(charge_point[EVSE_ID], True)


def check_boost_availability(charge_point: dict[str, Any]) -> bool:
    """Check if the boost button must be enabled."""
    activity: str = charge_point[ACTIVITY]
    vehicle_status = charge_point.get(VEHICLE_STATUS)

    if charge_point[SMART_CHARGING] and vehicle_status != VEHICLE_ERROR:
        if charge_point[DELAYED_CHARGING][VALUE]:
            return activity == DELAYED
        if charge_point[PRICE_BASED_CHARGING][VALUE]:
            return activity == CHARGING

    return False


CHARGE_POINT_BUTTONS = (
    ChargePointButtonEntityDescription(
        key="reset",
        translation_key="reset",
        function=lambda client, charge_point: client.reset(charge_point[EVSE_ID]),
        device_class=ButtonDeviceClass.RESTART,
    ),
    ChargePointButtonEntityDescription(
        key="reboot",
        translation_key="reboot",
        function=lambda client, charge_point: client.reboot(charge_point[EVSE_ID]),
        device_class=ButtonDeviceClass.RESTART,
    ),
    ChargePointButtonEntityDescription(
        key="stop_charge_session",
        translation_key="stop_charge_session",
        function=lambda client, charge_point: client.stop_session(
            charge_point[EVSE_ID]
        ),
    ),
    ChargePointButtonEntityDescription(
        key="boost",
        translation_key="boost",
        function=boost_charge_session,
        is_button_available=check_boost_availability,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BlueCurrentConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Blue Current buttons."""
    connector: Connector = entry.runtime_data
    async_add_entities(
        ChargePointButton(
            connector,
            button,
            evse_id,
        )
        for evse_id in connector.charge_points
        for button in CHARGE_POINT_BUTTONS
    )


class ChargePointButton(ChargepointEntity, ButtonEntity):
    """Define a charge point button."""

    has_value = True
    entity_description: ChargePointButtonEntityDescription

    def __init__(
        self,
        connector: Connector,
        description: ChargePointButtonEntityDescription,
        evse_id: str,
    ) -> None:
        """Initialize the button."""
        super().__init__(connector, evse_id)

        self.entity_description = description
        self._attr_unique_id = f"{description.key}_{evse_id}"

    async def async_press(self) -> None:
        """Handle the button press."""
        charge_point = self.connector.charge_points[self.evse_id]
        await self.entity_description.function(self.connector.client, charge_point)

    @callback
    def update_from_latest_data(self) -> None:
        """Fetch new state data for the button."""
        if self.entity_description.is_button_available:
            charge_point = self.connector.charge_points[self.evse_id]
            self.has_value = self.entity_description.is_button_available(charge_point)
