"""The HomeBrainz integration."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
import json
import voluptuous as vol

import aiohttp
import async_timeout
import websockets
from websockets.exceptions import WebSocketException, ConnectionClosedError
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback, ServiceCall
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

UPDATE_INTERVAL = timedelta(seconds=30)  # Fallback polling interval
WEBSOCKET_RETRY_DELAY = 10  # seconds
WEBSOCKET_MAX_RETRIES = 5

# Service schemas
SERVICE_SET_BRIGHTNESS = "set_brightness"
SERVICE_DISPLAY_TEXT = "display_text"
SERVICE_RESTART_DEVICE = "restart_device"

BRIGHTNESS_SCHEMA = vol.Schema({
    vol.Required("device_id"): str,
    vol.Required("brightness"): vol.Coerce(int),
})

DISPLAY_TEXT_SCHEMA = vol.Schema({
    vol.Required("device_id"): str,
    vol.Required("text"): str,
})

RESTART_DEVICE_SCHEMA = vol.Schema({
    vol.Required("device_id"): str,
})


class HomeBrainzDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the HomeBrainz device via WebSocket."""

    def __init__(self, hass: HomeAssistant, host: str) -> None:
        """Initialize."""
        self.host = host
        self.session = async_get_clientsession(hass)
        self._websocket = None
        self._websocket_url = f"ws://{host}/ws"
        self._retry_count = 0
        self._websocket_task = None
        self._websocket_connected = False
        
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,  # Fallback polling
        )

    async def async_start_websocket(self):
        """Start the WebSocket connection."""
        if self._websocket_task is None or self._websocket_task.done():
            self._websocket_task = asyncio.create_task(self._websocket_handler())

    async def async_stop_websocket(self):
        """Stop the WebSocket connection."""
        if self._websocket_task:
            self._websocket_task.cancel()
            try:
                await self._websocket_task
            except asyncio.CancelledError:
                pass
        
        if self._websocket:
            await self._websocket.close()
            self._websocket = None

    async def _websocket_handler(self):
        """Handle WebSocket connection and messages."""
        while True:
            try:
                _LOGGER.info("Attempting to connect to WebSocket at %s", self._websocket_url)
                
                async with websockets.connect(
                    self._websocket_url,
                    ping_interval=30,
                    ping_timeout=10,
                    close_timeout=10
                ) as websocket:
                    self._websocket = websocket
                    self._websocket_connected = True
                    self._retry_count = 0
                    
                    _LOGGER.info("WebSocket connected to HomeBrainz device")
                    
                    # Request initial data
                    await self._send_websocket_command({"command": "get_status"})
                    await self._send_websocket_command({"command": "get_sensors"})
                    
                    # Listen for messages
                    async for message in websocket:
                        try:
                            data = json.loads(message)
                            await self._handle_websocket_message(data)
                        except json.JSONDecodeError:
                            _LOGGER.warning("Received invalid JSON from WebSocket: %s", message)
                        except Exception as err:
                            _LOGGER.error("Error processing WebSocket message: %s", err)
                            
            except (WebSocketException, ConnectionClosedError, OSError) as err:
                self._websocket_connected = False
                self._websocket = None
                self._retry_count += 1
                
                if self._retry_count <= WEBSOCKET_MAX_RETRIES:
                    delay = min(WEBSOCKET_RETRY_DELAY * self._retry_count, 60)
                    _LOGGER.warning(
                        "WebSocket connection lost (%s), retrying in %d seconds (attempt %d/%d)",
                        err, delay, self._retry_count, WEBSOCKET_MAX_RETRIES
                    )
                    await asyncio.sleep(delay)
                else:
                    _LOGGER.error(
                        "WebSocket connection failed after %d attempts, falling back to HTTP polling",
                        WEBSOCKET_MAX_RETRIES
                    )
                    break
                    
            except asyncio.CancelledError:
                _LOGGER.debug("WebSocket handler cancelled")
                break
            except Exception as err:
                _LOGGER.error("Unexpected error in WebSocket handler: %s", err)
                await asyncio.sleep(WEBSOCKET_RETRY_DELAY)

    async def _send_websocket_command(self, command: dict):
        """Send a command to the WebSocket."""
        if self._websocket and not self._websocket.closed:
            try:
                await self._websocket.send(json.dumps(command))
                _LOGGER.debug("Sent WebSocket command: %s", command)
            except Exception as err:
                _LOGGER.error("Error sending WebSocket command: %s", err)

    async def _handle_websocket_message(self, data: dict):
        """Handle incoming WebSocket message."""
        message_type = data.get("type")
        
        if message_type == "sensor_update":
            # Real-time sensor data update
            sensor_data = data.get("data", {})
            status_data = {"uptime": data.get("timestamp", 0)}  # Basic status
            
            new_data = {
                "sensors": sensor_data,
                "status": status_data
            }
            
            # Update coordinator data immediately
            self.async_set_updated_data(new_data)
            _LOGGER.debug("Received real-time sensor update")
            
        elif message_type == "status_update":
            # Status update from device
            status_data = data.get("data", {})
            
            # If we have previous data, merge with status
            if self.data:
                new_data = self.data.copy()
                new_data["status"] = status_data
                self.async_set_updated_data(new_data)
            else:
                # First status update, request sensor data too
                await self._send_websocket_command({"command": "get_sensors"})
                
        elif message_type == "ping":
            # Respond to ping with pong
            await self._send_websocket_command({"type": "pong", "timestamp": data.get("timestamp")})
            
        elif data.get("command"):
            # Response to a command we sent
            command = data.get("command")
            success = data.get("success", False)
            
            if success and command == "get_sensors":
                sensor_data = data.get("data", {})
                if self.data:
                    new_data = self.data.copy()
                    new_data["sensors"] = sensor_data
                    self.async_set_updated_data(new_data)
                else:
                    self.async_set_updated_data({"sensors": sensor_data, "status": {}})
                    
            elif success and command == "get_status":
                status_data = data.get("data", {})
                if self.data:
                    new_data = self.data.copy()
                    new_data["status"] = status_data
                    self.async_set_updated_data(new_data)
                else:
                    self.async_set_updated_data({"sensors": {}, "status": status_data})

    async def send_device_command(self, command: str, **kwargs):
        """Send a command to the device."""
        if self._websocket_connected:
            cmd_data = {"command": command, **kwargs}
            await self._send_websocket_command(cmd_data)
            return True
        else:
            _LOGGER.warning("Cannot send command %s: WebSocket not connected", command)
            return False

    async def _async_update_data(self):
        """Update data via HTTP (fallback when WebSocket is not available)."""
        if self._websocket_connected:
            # WebSocket is handling updates, return current data
            return self.data
            
        try:
            async with async_timeout.timeout(10):
                # Fetch sensor data from the device
                async with self.session.get(f"http://{self.host}/sensors") as response:
                    if response.status == 200:
                        sensor_data = await response.json()
                    else:
                        raise UpdateFailed(f"Error communicating with device: {response.status}")
                
                # Fetch status data
                async with self.session.get(f"http://{self.host}/status") as response:
                    if response.status == 200:
                        status_data = await response.json()
                    else:
                        raise UpdateFailed(f"Error communicating with device: {response.status}")
                
                return {
                    "sensors": sensor_data,
                    "status": status_data
                }
                
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with API: {err}")
        except asyncio.TimeoutError:
            raise UpdateFailed("Timeout communicating with API")


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up HomeBrainz from a config entry."""
    coordinator = HomeBrainzDataUpdateCoordinator(
        hass, entry.data["host"]
    )

    await coordinator.async_config_entry_first_refresh()

    # Start WebSocket connection
    await coordinator.async_start_websocket()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Register services if this is the first entry
    if len(hass.data[DOMAIN]) == 1:
        await async_setup_services(hass)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    # Stop WebSocket connection
    await coordinator.async_stop_websocket()
    
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    # Unregister services if this was the last entry
    if not hass.data[DOMAIN]:
        await async_unload_services(hass)

    return unload_ok


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up services for HomeBrainz."""
    
    async def set_brightness_service(call: ServiceCall) -> None:
        """Handle set brightness service call."""
        device_id = call.data["device_id"]
        brightness = call.data["brightness"]
        
        coordinator = await _get_coordinator_for_device(hass, device_id)
        if coordinator:
            success = await coordinator.send_device_command("set_brightness", value=brightness)
            if success:
                _LOGGER.info("Set brightness to %d for device %s", brightness, device_id)
            else:
                _LOGGER.error("Failed to set brightness for device %s", device_id)
    
    async def display_text_service(call: ServiceCall) -> None:
        """Handle display text service call."""
        device_id = call.data["device_id"]
        text = call.data["text"]
        
        coordinator = await _get_coordinator_for_device(hass, device_id)
        if coordinator:
            success = await coordinator.send_device_command("display_text", text=text)
            if success:
                _LOGGER.info("Displayed text '%s' on device %s", text, device_id)
            else:
                _LOGGER.error("Failed to display text on device %s", device_id)
    
    async def restart_device_service(call: ServiceCall) -> None:
        """Handle restart device service call."""
        device_id = call.data["device_id"]
        
        coordinator = await _get_coordinator_for_device(hass, device_id)
        if coordinator:
            success = await coordinator.send_device_command("restart")
            if success:
                _LOGGER.info("Restart command sent to device %s", device_id)
            else:
                _LOGGER.error("Failed to restart device %s", device_id)
    
    hass.services.async_register(
        DOMAIN, SERVICE_SET_BRIGHTNESS, set_brightness_service, schema=BRIGHTNESS_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_DISPLAY_TEXT, display_text_service, schema=DISPLAY_TEXT_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_RESTART_DEVICE, restart_device_service, schema=RESTART_DEVICE_SCHEMA
    )


async def async_unload_services(hass: HomeAssistant) -> None:
    """Unload services for HomeBrainz."""
    hass.services.async_remove(DOMAIN, SERVICE_SET_BRIGHTNESS)
    hass.services.async_remove(DOMAIN, SERVICE_DISPLAY_TEXT)
    hass.services.async_remove(DOMAIN, SERVICE_RESTART_DEVICE)


async def _get_coordinator_for_device(hass: HomeAssistant, device_id: str) -> HomeBrainzDataUpdateCoordinator:
    """Get coordinator for a specific device."""
    device_registry = dr.async_get(hass)
    device = device_registry.async_get(device_id)
    
    if not device:
        _LOGGER.error("Device %s not found", device_id)
        return None
    
    # Find the config entry for this device
    for entry_id, coordinator in hass.data[DOMAIN].items():
        # Check if this coordinator handles this device
        if device.identifiers:
            for identifier in device.identifiers:
                if identifier[0] == DOMAIN:
                    # This should match the device info in sensors
                    return coordinator
    
    _LOGGER.error("No coordinator found for device %s", device_id)
    return None