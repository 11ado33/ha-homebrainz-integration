"""Select platform for HomeBrainz integration."""
from __future__ import annotations

from copy import deepcopy
import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import HomeBrainzDataUpdateCoordinator
from .const import DOMAIN, MANUFACTURER, MODEL

_LOGGER = logging.getLogger(__name__)

# Supported IANA timezones (must match ESP tz_lookup.h)
SUPPORTED_TIMEZONES = [
    "Etc/UTC",
    "Europe/London",
    "Europe/Dublin",
    "Europe/Lisbon",
    "Europe/Paris",
    "Europe/Berlin",
    "Europe/Rome",
    "Europe/Madrid",
    "Europe/Amsterdam",
    "Europe/Brussels",
    "Europe/Prague",
    "Europe/Vienna",
    "Europe/Warsaw",
    "Europe/Stockholm",
    "Europe/Oslo",
    "Europe/Copenhagen",
    "Europe/Helsinki",
    "Europe/Athens",
    "Europe/Istanbul",
    "Europe/Moscow",
    "Europe/Kiev",
    "America/New_York",
    "America/Chicago",
    "America/Denver",
    "America/Los_Angeles",
    "America/Toronto",
    "America/Vancouver",
    "America/Sao_Paulo",
    "America/Argentina/Buenos_Aires",
    "America/Mexico_City",
    "Asia/Tokyo",
    "Asia/Shanghai",
    "Asia/Hong_Kong",
    "Asia/Singapore",
    "Asia/Seoul",
    "Asia/Kolkata",
    "Asia/Dubai",
    "Asia/Bangkok",
    "Asia/Jakarta",
    "Asia/Manila",
    "Asia/Taipei",
    "Australia/Sydney",
    "Australia/Melbourne",
    "Australia/Perth",
    "Australia/Brisbane",
    "Pacific/Auckland",
    "Pacific/Honolulu",
    "Africa/Cairo",
    "Africa/Johannesburg",
    "Africa/Lagos",
    "Africa/Nairobi",
    "America/Santiago",
    "America/Lima",
    "America/Bogota",
    "America/Caracas",
    "America/La_Paz",
    "America/Montevideo",
    "Atlantic/Reykjavik",
    "Atlantic/Azores",
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the select platform."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([HomeBrainzTimezoneSelect(coordinator, config_entry)])


class HomeBrainzTimezoneSelect(CoordinatorEntity, SelectEntity):
    """Select entity for device timezone."""

    _attr_name = "Timezone"
    _attr_icon = "mdi:map-clock-outline"
    _attr_options = SUPPORTED_TIMEZONES

    def __init__(
        self,
        coordinator: HomeBrainzDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self.config_entry = config_entry
        self._host = config_entry.data["host"]
        self._attr_unique_id = f"{config_entry.entry_id}_timezone"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device_name = "HomeBrainz Clock"
        mac_address = ""

        status = {}
        if self.coordinator.data:
            status = self.coordinator.data.get("status", {}) or {}
            if isinstance(status, dict):
                device_name = status.get("device", device_name)
                mac_address = status.get("mac_address", mac_address)

        return DeviceInfo(
            identifiers={(DOMAIN, mac_address or self._host)},
            name=device_name,
            manufacturer=MANUFACTURER,
            model=MODEL,
            sw_version=status.get("version", "Unknown") if isinstance(status, dict) else "Unknown",
            configuration_url=f"http://{self._host}",
        )

    @property
    def current_option(self) -> str | None:
        """Return the current timezone."""
        if not self.coordinator.data:
            return None
        config = self.coordinator.data.get("config", {})
        if not isinstance(config, dict):
            return None
        tz = config.get("timeZone")
        if tz and tz in SUPPORTED_TIMEZONES:
            return tz
        return None

    async def async_select_option(self, option: str) -> None:
        """Set the timezone on the device."""
        if option not in SUPPORTED_TIMEZONES:
            raise HomeAssistantError(f"Unsupported timezone: {option}")

        success = await self.coordinator.async_set_timezone(option)
        if not success:
            raise HomeAssistantError("Unable to set timezone on HomeBrainz device.")
