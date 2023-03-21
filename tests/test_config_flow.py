"""Test the Blue Current config flow."""
from unittest.mock import patch

from homeassistant import config_entries
from homeassistant.components.blue_current import DOMAIN
from homeassistant.components.blue_current.config_flow import (
    AlreadyConnected,
    InvalidApiToken,
    NoCardsFound,
    RequestLimitReached,
    WebsocketException,
)
from homeassistant.config_entries import SOURCE_REAUTH
from homeassistant.const import CONF_SOURCE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry


async def test_form(hass: HomeAssistant) -> None:
    """Test if the form is created."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["errors"] == {}


async def test_default_card(hass: HomeAssistant) -> None:
    """Test if the default card is set."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["errors"] == {}

    with patch("bluecurrent_api.Client.validate_api_token", return_value=True), patch(
        "bluecurrent_api.Client.get_email", return_value="test@email.com"
    ), patch(
        "homeassistant.components.blue_current.async_setup_entry",
        return_value=True,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "api_token": "123",
            },
        )
        await hass.async_block_till_done()

    assert result2["title"] == "123"
    assert result2["data"] == {"api_token": "123", "card": "BCU_APP"}


async def test_user_card(hass: HomeAssistant) -> None:
    """Test if the user can set a custom card."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["errors"] == {}

    with patch("bluecurrent_api.Client.validate_api_token", return_value=True,), patch(
        "bluecurrent_api.Client.get_email", return_value="test@email.com"
    ), patch(
        "bluecurrent_api.Client.get_charge_cards",
        return_value=[{"name": "card 1", "uid": 1}, {"name": "card 2", "uid": 2}],
    ), patch(
        "homeassistant.components.blue_current.async_setup_entry",
        return_value=True,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"api_token": "123", "add_card": True},
        )
        await hass.async_block_till_done()

    with patch(
        "bluecurrent_api.Client.get_charge_cards",
        return_value=[{"name": "card 1", "uid": 1}, {"name": "card 2", "uid": 2}],
    ), patch(
        "homeassistant.components.blue_current.async_setup_entry",
        return_value=True,
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {"card": "card 1"},
        )
        await hass.async_block_till_done()

    assert result3["title"] == "123"
    assert result3["data"] == {"api_token": "123", "card": 1}


async def test_form_invalid_token(hass: HomeAssistant) -> None:
    """Test if an invalid api token is handled."""
    with patch(
        "bluecurrent_api.Client.validate_api_token",
        side_effect=InvalidApiToken,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={"api_token": "123"},
        )
        assert result["errors"] == {"base": "invalid_token"}


async def test_form_limit_reached(hass: HomeAssistant) -> None:
    """Test if an limit reached error is handled."""
    with patch(
        "bluecurrent_api.Client.validate_api_token",
        side_effect=RequestLimitReached,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={"api_token": "123"},
        )
        assert result["errors"] == {"base": "limit_reached"}


async def test_form_already_connected(hass: HomeAssistant) -> None:
    """Test if an already connected error is handled."""
    with patch(
        "bluecurrent_api.Client.validate_api_token",
        side_effect=AlreadyConnected,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={"api_token": "123"},
        )
        assert result["errors"] == {"base": "already_connected"}


async def test_form_exception(hass: HomeAssistant) -> None:
    """Test if an exception is handled."""
    with patch(
        "bluecurrent_api.Client.validate_api_token",
        side_effect=Exception,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={"api_token": "123"},
        )
        assert result["errors"] == {"base": "unknown"}


async def test_form_cannot_connect(hass: HomeAssistant) -> None:
    """Test if a connection error is handled."""

    with patch(
        "bluecurrent_api.Client.validate_api_token",
        side_effect=WebsocketException,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={"api_token": "123"},
        )
        assert result["errors"] == {"base": "cannot_connect"}


async def test_form_no_cards_found(hass: HomeAssistant) -> None:
    """Test if a no cards error is handled."""

    with patch("bluecurrent_api.Client.validate_api_token", return_value=True,), patch(
        "bluecurrent_api.Client.get_email", return_value="test@email.com"
    ), patch(
        "bluecurrent_api.Client.get_charge_cards",
        side_effect=NoCardsFound,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={"api_token": "123", "add_card": True},
        )

        assert result["errors"] == {"base": "no_cards_found"}


async def test_form_cannot_connect_card(hass: HomeAssistant) -> None:
    """Test if a connection error on get_charge_cards is handled."""

    with patch("bluecurrent_api.Client.validate_api_token", return_value=True,), patch(
        "bluecurrent_api.Client.get_email", return_value="test@email.com"
    ), patch(
        "bluecurrent_api.Client.get_charge_cards",
        side_effect=WebsocketException,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={"api_token": "123", "add_card": True},
        )

        assert result["errors"] == {"base": "cannot_connect"}


async def test_form_limit_reached_card(hass: HomeAssistant) -> None:
    """Test if an limit reached error is handled."""
    with patch("bluecurrent_api.Client.validate_api_token", return_value=True,), patch(
        "bluecurrent_api.Client.get_email", return_value="test@email.com"
    ), patch(
        "bluecurrent_api.Client.get_charge_cards",
        side_effect=RequestLimitReached,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={"api_token": "123", "add_card": True},
        )
        assert result["errors"] == {"base": "limit_reached"}


async def test_form_already_connected_card(hass: HomeAssistant) -> None:
    """Test if an already connected error is handled."""
    with patch("bluecurrent_api.Client.validate_api_token", return_value=True,), patch(
        "bluecurrent_api.Client.get_email", return_value="test@email.com"
    ), patch(
        "bluecurrent_api.Client.get_charge_cards",
        side_effect=AlreadyConnected,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={"api_token": "123", "add_card": True},
        )
        assert result["errors"] == {"base": "already_connected"}


async def test_form_exception_card(hass: HomeAssistant) -> None:
    """Test if an exception is handled."""
    with patch("bluecurrent_api.Client.validate_api_token", return_value=True,), patch(
        "bluecurrent_api.Client.get_email", return_value="test@email.com"
    ), patch(
        "bluecurrent_api.Client.get_charge_cards",
        side_effect=Exception,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={"api_token": "123", "add_card": True},
        )
        assert result["errors"] == {"base": "unknown"}


async def test_flow_reauth(hass: HomeAssistant):
    """Test reauth step."""
    with patch(
        "bluecurrent_api.Client.validate_api_token",
        return_value=True,
    ), patch("bluecurrent_api.Client.get_email", return_value="test@email.com"):
        entry = MockConfigEntry(
            domain=DOMAIN,
            entry_id="uuid",
            unique_id="test@email.com",
            data={"api_token": "123"},
        )
        entry.add_to_hass(hass)
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={
                CONF_SOURCE: SOURCE_REAUTH,
                "entry_id": entry.entry_id,
                "unique_id": entry.unique_id,
            },
            data={"api_token": "abc"},
        )

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "user"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"api_token": "1234567890"},
        )
        assert result["type"] == FlowResultType.ABORT
        assert result["reason"] == "reauth_successful"
        assert entry.data.copy() == {"api_token": "1234567890"}
