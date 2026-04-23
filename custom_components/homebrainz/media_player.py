"""Media player platform for HomeBrainz integration."""
from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlparse, urlunparse

from homeassistant.components.media_player import MediaPlayerEntity
from homeassistant.components.media_player.const import (
    MediaPlayerEntityFeature,
    MediaPlayerState,
    MediaType,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.network import get_url
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import HomeBrainzDataUpdateCoordinator
from .const import DOMAIN, MANUFACTURER, MODEL

_LOGGER = logging.getLogger(__name__)

SPEAKER_FEATURES = (
    MediaPlayerEntityFeature.VOLUME_SET
    | MediaPlayerEntityFeature.VOLUME_MUTE
    | MediaPlayerEntityFeature.PLAY
    | MediaPlayerEntityFeature.PAUSE
    | MediaPlayerEntityFeature.STOP
    | MediaPlayerEntityFeature.PLAY_MEDIA
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the media_player platform."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([HomeBrainzSpeakerEntity(coordinator, config_entry)])


class HomeBrainzSpeakerEntity(CoordinatorEntity, MediaPlayerEntity):
    """HomeBrainz speaker exposed as a Home Assistant media player."""

    _attr_name = "Speaker"
    _attr_supported_features = SPEAKER_FEATURES

    def __init__(
        self,
        coordinator: HomeBrainzDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the media player entity."""
        super().__init__(coordinator)
        self.config_entry = config_entry
        self._host = config_entry.data["host"]
        self._attr_unique_id = f"{config_entry.entry_id}_speaker"

        # Optimistic fallback state for older firmware responses.
        self._optimistic_state = MediaPlayerState.IDLE
        self._optimistic_volume_level = 0.5
        self._optimistic_is_muted = False

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

    def _status(self) -> dict[str, Any]:
        if not self.coordinator.data:
            return {}
        status = self.coordinator.data.get("status", {})
        return status if isinstance(status, dict) else {}

    def _speaker_data(self) -> dict[str, Any]:
        status = self._status()
        speaker = status.get("speaker", {})
        if isinstance(speaker, dict):
            return speaker

        # Atmos firmware reports speaker values as top-level status keys.
        merged: dict[str, Any] = {}
        if "speaker_playing" in status:
            merged["playing"] = status.get("speaker_playing")
        if "speaker_muted" in status:
            merged["muted"] = status.get("speaker_muted")
        if "speaker_volume" in status:
            merged["volume"] = status.get("speaker_volume")
        if "speaker_available" in status:
            merged["available"] = status.get("speaker_available")
        return merged

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    @property
    def state(self) -> MediaPlayerState:
        """Return the current playback state."""
        status = self._status()
        speaker = self._speaker_data()

        raw_state = (
            speaker.get("state")
            or status.get("speaker_state")
            or status.get("media_state")
        )

        if isinstance(raw_state, str):
            normalized = raw_state.strip().lower()
            if normalized == "playing":
                return MediaPlayerState.PLAYING
            if normalized == "paused":
                return MediaPlayerState.PAUSED
            if normalized in ("off", "idle", "stopped", "stop"):
                return MediaPlayerState.IDLE
            if normalized == "unavailable":
                return MediaPlayerState.OFF

        raw_playing = speaker.get("playing")
        if isinstance(raw_playing, bool):
            return MediaPlayerState.PLAYING if raw_playing else MediaPlayerState.IDLE

        raw_available = speaker.get("available")
        if isinstance(raw_available, bool) and not raw_available:
            return MediaPlayerState.OFF

        return self._optimistic_state

    @property
    def volume_level(self) -> float | None:
        """Volume level in range 0.0..1.0."""
        status = self._status()
        speaker = self._speaker_data()

        raw_volume = speaker.get("volume")
        if raw_volume is None:
            raw_volume = status.get("speaker_volume")

        if isinstance(raw_volume, (int, float)):
            if raw_volume > 1:
                return max(0.0, min(1.0, float(raw_volume) / 100.0))
            return max(0.0, min(1.0, float(raw_volume)))

        return self._optimistic_volume_level

    @property
    def is_volume_muted(self) -> bool | None:
        """Return muted state."""
        status = self._status()
        speaker = self._speaker_data()

        raw_muted = speaker.get("muted")
        if raw_muted is None:
            raw_muted = status.get("speaker_muted")

        if isinstance(raw_muted, bool):
            return raw_muted

        return self._optimistic_is_muted

    @property
    def media_title(self) -> str | None:
        """Return current media title when available."""
        status = self._status()
        speaker = self._speaker_data()
        title = speaker.get("title") or status.get("media_title")
        return title if isinstance(title, str) else None

    async def async_mute_volume(self, mute: bool) -> None:
        """Mute/unmute playback."""
        success = await self.coordinator.async_speaker_command("mute", muted=mute)
        if success:
            self._optimistic_is_muted = mute
            self.async_write_ha_state()

    async def async_set_volume_level(self, volume: float) -> None:
        """Set volume level."""
        volume = max(0.0, min(1.0, volume))
        percent = int(round(volume * 100))
        success = await self.coordinator.async_speaker_command("set_volume", value=percent)
        if success:
            self._optimistic_volume_level = volume
            self.async_write_ha_state()

    async def async_media_play(self) -> None:
        """Resume playback."""
        success = await self.coordinator.async_speaker_command("play")
        if success:
            self._optimistic_state = MediaPlayerState.PLAYING
            self.async_write_ha_state()

    async def async_media_pause(self) -> None:
        """Pause playback."""
        success = await self.coordinator.async_speaker_command("pause")
        if success:
            # Current firmware maps pause to stop.
            self._optimistic_state = MediaPlayerState.IDLE
            self.async_write_ha_state()

    async def async_media_stop(self) -> None:
        """Stop playback."""
        success = await self.coordinator.async_speaker_command("stop")
        if success:
            self._optimistic_state = MediaPlayerState.IDLE
            self.async_write_ha_state()

    async def async_play_media(
        self,
        media_type: MediaType | str,
        media_id: str,
        **kwargs: Any,
    ) -> None:
        """Play media by id/url."""
        resolved_media_id = await self._resolve_media_id(media_id)

        payload: dict[str, Any] = {
            "media_type": str(media_type),
            "media_id": resolved_media_id,
        }

        announce = kwargs.get("announce")
        if isinstance(announce, bool):
            payload["announce"] = announce

        enqueue = kwargs.get("enqueue")
        if enqueue is not None:
            payload["enqueue"] = str(enqueue)

        success = await self.coordinator.async_speaker_command("play_media", **payload)
        if success:
            self._optimistic_state = MediaPlayerState.PLAYING
            self.async_write_ha_state()

    async def _resolve_media_id(self, media_id: str) -> str:
        """Resolve Home Assistant media IDs to a concrete URL the device can fetch."""
        resolved = media_id

        if media_id.startswith("media-source://"):
            try:
                from homeassistant.components.media_source import async_resolve_media

                media = await async_resolve_media(self.hass, media_id, self.entity_id)
                resolved = media.url
            except Exception:
                # Keep original id; coordinator/firmware will log error if unusable.
                return media_id

        if resolved.startswith("/"):
            try:
                base = get_url(self.hass, prefer_external=False)
                resolved = f"{base}{resolved}"
            except Exception:
                return resolved

        try:
            from homeassistant.components.media_player.browse_media import async_process_play_media_url

            resolved = async_process_play_media_url(self.hass, resolved)
        except Exception:
            pass

        # Atmos firmware currently supports plain HTTP stream URLs only.
        if resolved.startswith("https://"):
            parsed = urlparse(resolved)
            resolved = urlunparse(parsed._replace(scheme="http"))
            _LOGGER.debug("Converted HTTPS media URL to HTTP for Atmos device compatibility: %s", resolved)

        if not resolved.startswith("http://"):
            _LOGGER.warning(
                "Unsupported media URL for Atmos speaker (requires http://): %s",
                resolved,
            )

        return resolved
