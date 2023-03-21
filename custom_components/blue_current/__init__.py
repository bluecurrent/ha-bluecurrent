"""The Blue Current integration."""
from __future__ import annotations

from contextlib import suppress
from datetime import datetime
from typing import Any

from bluecurrent_api import Client
from bluecurrent_api.exceptions import (
    BlueCurrentException,
    InvalidApiToken,
    RequestLimitReached,
    WebsocketException,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_TOKEN, EVENT_HOMEASSISTANT_STOP, Platform
from homeassistant.core import Event, HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import entity_registry
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_call_later

from .const import CARD, DOMAIN, EVSE_ID, LOGGER, MODEL_TYPE

PLATFORMS = [Platform.SENSOR, Platform.SWITCH, Platform.BUTTON]
CHARGE_POINTS = "CHARGE_POINTS"
DATA = "data"
SMALL_DELAY = 1
LARGE_DELAY = 20

GRID = "GRID"
OBJECT = "object"
VALUE_TYPES = ("CH_STATUS", "CH_SETTINGS")
SETTINGS = ("PUBLIC_CHARGING", "PLUG_AND_CHARGE")
RESULT = "result"
ACTIVITY = "activity"
UNAVAILABLE = "unavailable"
OPERATIVE = "operative"
SERVICES = ("SOFT_RESET", "REBOOT", "START_SESSION", "STOP_SESSION")
SUCCESS = "success"
RESET = "reset"
REBOOT = "reboot"
START_SESSION = "start_session"
STOP_SESSION = "stop_session"


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up Blue Current as a config entry."""
    hass.data.setdefault(DOMAIN, {})
    client = Client()
    api_token = config_entry.data[CONF_API_TOKEN]
    connector = Connector(hass, config_entry, client)
    try:
        await connector.connect(api_token)
    except InvalidApiToken as err:
        raise ConfigEntryAuthFailed("Invalid API token.") from err
    except BlueCurrentException as err:
        raise ConfigEntryNotReady from err

    hass.loop.create_task(connector.start_loop())
    await client.get_charge_points()

    await client.wait_for_response()
    hass.data[DOMAIN][config_entry.entry_id] = connector
    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    async def _async_disconnect_websocket(_: Event) -> None:
        await connector.disconnect()

    config_entry.async_on_unload(
        hass.bus.async_listen_once(
            EVENT_HOMEASSISTANT_STOP, _async_disconnect_websocket
        )
    )

    async def handle_reset(call: ServiceCall) -> None:
        evse_id = call.data.get(EVSE_ID)
        await client.reset(evse_id)

    async def handle_reboot(call: ServiceCall) -> None:
        evse_id = call.data.get(EVSE_ID)
        await client.reboot(evse_id)

    async def handle_start_session(call: ServiceCall) -> None:
        evse_id = call.data.get(EVSE_ID)
        await client.start_session(evse_id, config_entry.data[CARD])

    async def handle_stop_session(call: ServiceCall) -> None:
        evse_id = call.data.get(EVSE_ID)
        await client.stop_session(evse_id)

    hass.services.async_register(DOMAIN, "reset", handle_reset)
    hass.services.async_register(DOMAIN, "reboot", handle_reboot)
    hass.services.async_register(DOMAIN, "start_session", handle_start_session)
    hass.services.async_register(DOMAIN, "stop_session", handle_stop_session)

    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload the Blue Current config entry."""
    connector: Connector = hass.data[DOMAIN].pop(config_entry.entry_id)
    hass.async_create_task(connector.disconnect())

    return await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)


def set_entities_unavalible(hass: HomeAssistant, config_id: str) -> None:
    """Set all Blue Current entities to unavailable."""
    registry = entity_registry.async_get(hass)
    entries = entity_registry.async_entries_for_config_entry(registry, config_id)

    for entry in entries:
        entry.write_unavailable_state(hass)


class Connector:
    """Define a class that connects to the Blue Current websocket API."""

    def __init__(
        self, hass: HomeAssistant, config: ConfigEntry, client: Client
    ) -> None:
        """Initialize."""
        self.config: ConfigEntry = config
        self.hass: HomeAssistant = hass
        self.client: Client = client
        self.charge_points: dict[str, dict] = {}
        self.grid: dict[str, Any] = {}

    async def connect(self, token: str) -> None:
        """Register on_data and connect to the websocket."""
        await self.client.connect(token)

    async def on_data(self, message: dict) -> None:
        """Handle received data."""

        async def handle_charge_points(data: list) -> None:
            """Loop over the charge points and get their data."""
            for entry in data:
                evse_id = entry[EVSE_ID]
                model = entry[MODEL_TYPE]
                self.add_charge_point(evse_id, model)
                await self.get_charge_point_data(evse_id)
            await self.client.get_grid_status(data[0][EVSE_ID])

        object_name: str = message[OBJECT]

        # gets charge point ids
        if object_name == CHARGE_POINTS:
            charge_points_data: list = message[DATA]
            await handle_charge_points(charge_points_data)

        # gets charge point key / values
        elif object_name in VALUE_TYPES:
            value_data: dict = message[DATA]
            evse_id = value_data.pop(EVSE_ID)
            self.update_charge_point(evse_id, value_data)

        # gets grid key / values
        elif GRID in object_name:
            data: dict = message[DATA]
            self.grid = data
            self.dispatch_grid_update_signal()

        # setting change responses
        elif object_name in SETTINGS:
            evse_id = message.pop(EVSE_ID)
            key = object_name.lower()
            result = message[RESULT]
            new_data = {key: result}
            self.update_charge_point(evse_id, new_data)

        # service responses
        elif object_name in SERVICES:
            state = "successful"
            success: bool = message[SUCCESS]
            if not success:
                state = "un" + state
            LOGGER.debug("%s was %s ", object_name, state)

    async def get_charge_point_data(self, evse_id: str) -> None:
        """Get all the data of a charge point."""
        await self.client.get_status(evse_id)
        await self.client.get_settings(evse_id)

    def add_charge_point(self, evse_id: str, model: str) -> None:
        """Add a charge point to charge_points."""
        self.charge_points[evse_id] = {MODEL_TYPE: model}

    def update_charge_point(self, evse_id: str, data: dict) -> None:
        """Update the charge point data."""

        def handle_activity(data: dict) -> None:
            activity = data.get(ACTIVITY)
            if activity != UNAVAILABLE:
                data[OPERATIVE] = True
            else:
                data[OPERATIVE] = False

        if ACTIVITY in data:
            handle_activity(data)

        self.charge_points[evse_id].update(data)
        self.dispatch_value_update_signal(evse_id)

    def dispatch_value_update_signal(self, evse_id: str) -> None:
        """Dispatch a value signal."""
        async_dispatcher_send(self.hass, f"{DOMAIN}_value_update_{evse_id}")

    def dispatch_grid_update_signal(self) -> None:
        """Dispatch a grid signal."""
        async_dispatcher_send(self.hass, f"{DOMAIN}_grid_update")

    async def start_loop(self) -> None:
        """Start the receive loop."""
        try:
            await self.client.start_loop(self.on_data)
        except BlueCurrentException as err:
            LOGGER.warning(
                "Disconnected from the Blue Current websocket. Retrying to connect in background. %s",
                err,
            )

            async_call_later(self.hass, SMALL_DELAY, self.reconnect)

    async def reconnect(self, event_time: datetime | None = None) -> None:
        """Keep trying to reconnect to the websocket."""
        try:
            await self.connect(self.config.data[CONF_API_TOKEN])
            LOGGER.info("Reconnected to the Blue Current websocket")
            self.hass.loop.create_task(self.start_loop())
            await self.client.get_charge_points()
        except RequestLimitReached:
            set_entities_unavalible(self.hass, self.config.entry_id)
            async_call_later(
                self.hass, self.client.get_next_reset_delta(), self.reconnect
            )
        except WebsocketException:
            set_entities_unavalible(self.hass, self.config.entry_id)
            async_call_later(self.hass, LARGE_DELAY, self.reconnect)

    async def disconnect(self) -> None:
        """Disconnect from the websocket."""
        with suppress(WebsocketException):
            await self.client.disconnect()
