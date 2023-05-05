"""The tests for Blue Current buttons."""

from datetime import datetime
from unittest.mock import patch

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util

from . import init_integration

data = {
    "101": {
        "model_type": "hidden",
        "evse_id": "101",
    }
}

buttons = ("start_session", "stop_session", "reset", "reboot")


async def test_buttons(hass: HomeAssistant):
    """Test the underlying buttons."""
    await init_integration(hass, "button", data)

    entity_registry = er.async_get(hass)

    for button in buttons:
        state = hass.states.get(f"button.101_{button}")
        assert state is not None
        assert state.state == "unknown"
        entry = entity_registry.async_get(f"button.101_{button}")
        assert entry and entry.unique_id == f"{button}_101"

        now = dt_util.parse_datetime("2021-01-09 12:00:00+00:00")
        assert isinstance(now, datetime)
        with patch("homeassistant.util.dt.utcnow", return_value=now):
            await hass.services.async_call(
                "button",
                "press",
                {"entity_id": f"button.101_{button}"},
                blocking=True,
            )

        state = hass.states.get(f"button.101_{button}")
        assert state
        assert state.state == now.isoformat()

        created_buttons = er.async_entries_for_config_entry(entity_registry, "uuid")
        assert len(buttons) == len(created_buttons)
