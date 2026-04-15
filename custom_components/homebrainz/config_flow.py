"""Config flow for HomeBrainz integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import async_timeout
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

try:
    # Newer Home Assistant versions
    from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo
except ImportError:  # pragma: no cover - fallback for older HA cores
    from homeassistant.components.zeroconf import ZeroconfServiceInfo

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
    }
)


def normalize_host(host: str) -> str:
    """Normalize user/discovery host input to a plain host value."""
    normalized_host = host.strip()

    if normalized_host.startswith(("http://", "https://")):
        normalized_host = normalized_host.split("://", 1)[1]

    return normalized_host.rstrip("/").rstrip(".")


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    host = normalize_host(data[CONF_HOST])
    
    session = async_get_clientsession(hass)
    
    try:
        async with async_timeout.timeout(10):
            # Test connection to the device
            async with session.get(f"http://{host}/status") as response:
                if response.status != 200:
                    raise CannotConnect
                
                status_data = await response.json()
                
                # Verify it's a HomeBrainz Clock device by checking for expected fields
                if "device" not in status_data:
                    raise InvalidDevice
                
                # Get device info for unique ID
                device_name = status_data.get("device", "HomeBrainz Clock")
                mac_address = status_data.get("mac_address", "")
                
                return {
                    "title": device_name,
                    "host": host,
                    "mac_address": mac_address,
                }
                
    except InvalidDevice:
        raise
    except aiohttp.ClientError:
        raise CannotConnect
    except Exception:
        _LOGGER.exception("Unexpected exception")
        raise CannotConnect


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HomeBrainz."""

    VERSION = 3

    async def async_step_zeroconf(
        self,
        discovery_info: ZeroconfServiceInfo,
    ) -> FlowResult:
        """Handle Zeroconf discovery."""
        host = discovery_info.host
        if not host:
            return self.async_abort(reason="cannot_connect")

        try:
            info = await validate_input(self.hass, {CONF_HOST: host})
        except CannotConnect:
            return self.async_abort(reason="cannot_connect")
        except InvalidDevice:
            return self.async_abort(reason="invalid_device")

        unique_id = info["mac_address"] if info["mac_address"] else info["host"]
        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=info["title"],
            data={CONF_HOST: info["host"]},
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidDevice:
                errors["base"] = "invalid_device"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                # Create a unique ID based on MAC address if available
                unique_id = info["mac_address"] if info["mac_address"] else info["host"]
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()
                
                return self.async_create_entry(
                    title=info["title"],
                    data={CONF_HOST: info["host"]},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidDevice(HomeAssistantError):
    """Error to indicate the device is not a valid HomeBrainz Clock device."""