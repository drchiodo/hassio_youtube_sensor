"""Config flow for YouTube Sensor integration."""
from __future__ import annotations

import logging
import voluptuous as vol
from typing import Any

import homeassistant.helpers.config_validation as cv
from homeassistant.config_entries import ConfigFlow
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_create_clientsession
import async_timeout

from .const import DOMAIN, CONF_CHANNEL_ID, CONF_INCLUDE_SHORTS

_LOGGER = logging.getLogger(__name__)

BASE_URL = 'https://www.youtube.com/feeds/videos.xml?channel_id={}'

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_CHANNEL_ID): cv.string,
        vol.Optional(CONF_NAME): cv.string,
        vol.Optional(CONF_INCLUDE_SHORTS, default=False): cv.boolean,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    
    channel_id = data[CONF_CHANNEL_ID].strip()
    
    # Verifica che il channel_id inizi con UC
    if not channel_id.startswith("UC"):
        raise InvalidChannelId("Channel ID must start with 'UC'")
    
    # Verifica che il channel_id abbia la lunghezza corretta (24 caratteri)
    if len(channel_id) != 24:
        raise InvalidChannelId("Channel ID must be 24 characters long")
    
    # Testa la connettività al canale
    session = async_create_clientsession(hass)
    
    try:
        url = BASE_URL.format(channel_id)
        async with async_timeout.timeout(10):
            response = await session.get(url)
            info = await response.text()
        
        # Verifica che la risposta contenga dati validi
        if '<title>' not in info or 'channel' not in info.lower():
            raise CannotConnect("Unable to fetch channel data")
        
        # Estrai il nome del canale dal feed
        try:
            channel_name = info.split('<title>')[1].split('</')[0]
        except (IndexError, AttributeError):
            channel_name = f"Channel {channel_id}"
        
        # Se l'utente non ha fornito un nome, usa quello del canale
        if not data.get(CONF_NAME):
            data[CONF_NAME] = channel_name
            
    except Exception as exc:
        _LOGGER.error("Error validating channel %s: %s", channel_id, exc)
        raise CannotConnect("Cannot connect to YouTube channel") from exc
    
    # Restituisci i dati validati
    return {
        "title": data[CONF_NAME],
        CONF_CHANNEL_ID: channel_id,
        CONF_NAME: data[CONF_NAME],
        CONF_INCLUDE_SHORTS: data.get(CONF_INCLUDE_SHORTS, False),
    }


class YouTubeSensorConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for YouTube Sensor."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", 
                data_schema=STEP_USER_DATA_SCHEMA,
                description_placeholders={
                    "channel_id_example": "UC4V3oCikXeSqYQr0hBMARwg",
                }
            )

        errors = {}

        try:
            info = await validate_input(self.hass, user_input)
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except InvalidChannelId as exc:
            errors["channel_id"] = "invalid_channel_id"
            _LOGGER.error("Invalid channel ID: %s", exc)
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            # Crea un unique_id basato sul channel_id per evitare duplicati
            await self.async_set_unique_id(user_input[CONF_CHANNEL_ID])
            self._abort_if_unique_id_configured()
            
            return self.async_create_entry(title=info["title"], data=info)

        return self.async_show_form(
            step_id="user", 
            data_schema=STEP_USER_DATA_SCHEMA, 
            errors=errors,
            description_placeholders={
                "channel_id_example": "UC4V3oCikXeSqYQr0hBMARwg",
            }
        )

    async def async_step_import(self, user_input: dict[str, Any]) -> FlowResult:
        """Handle import from configuration.yaml."""
        # Permette di importare configurazioni esistenti da configuration.yaml
        try:
            info = await validate_input(self.hass, user_input)
        except (CannotConnect, InvalidChannelId):
            _LOGGER.error("Cannot import YouTube sensor config for channel %s", 
                         user_input.get(CONF_CHANNEL_ID))
            return self.async_abort(reason="cannot_connect")
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception during import")
            return self.async_abort(reason="unknown")

        await self.async_set_unique_id(user_input[CONF_CHANNEL_ID])
        self._abort_if_unique_id_configured()
        
        return self.async_create_entry(title=info["title"], data=info)


class CannotConnect(Exception):
    """Error to indicate we cannot connect."""


class InvalidChannelId(Exception):
    """Error to indicate the channel ID is invalid."""