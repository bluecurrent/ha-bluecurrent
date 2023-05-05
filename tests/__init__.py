"""Tests for the Blue Current integration."""
from __future__ import annotations

from unittest.mock import patch

from bluecurrent_api import Client
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.blue_current import DOMAIN, Connector


async def init_integration(
    hass: HomeAssistant, platform, data: dict, grid=None
) -> MockConfigEntry:
    """Set up the Blue Current integration in Home Assistant."""

    if grid is None:
        grid = {}

    def init(
        self: Connector, hass: HomeAssistant, config: ConfigEntry, client: Client
    ) -> None:
        """Mock grid and charge_points."""

        self.config = config
        self.hass = hass
        self.client = client
        self.charge_points = data
        self.grid = grid

    with patch(
        "custom_components.blue_current.PLATFORMS", [platform]
    ), patch.object(Connector, "__init__", init), patch(
        "custom_components.blue_current.Client", autospec=True
    ):
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            entry_id="uuid",
            unique_id="uuid",
            data={"api_token": "123", "card": {"123"}},
        )
        config_entry.add_to_hass(hass)

        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
        async_dispatcher_send(hass, "blue_current_value_update_101")
    return config_entry
