"""Sensor platform for HomeBrainz integration."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    UnitOfPressure,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import HomeBrainzDataUpdateCoordinator
from .const import DOMAIN, MANUFACTURER, MODEL


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = [
        HomeBrainzTemperatureSensor(coordinator, config_entry),
        HomeBrainzHumiditySensor(coordinator, config_entry),
        HomeBrainzPressureSensor(coordinator, config_entry),
        HomeBrainzAQISensor(coordinator, config_entry),
        HomeBrainzCO2Sensor(coordinator, config_entry),
        HomeBrainzTVOCSensor(coordinator, config_entry),
        HomeBrainzWiFiSignalSensor(coordinator, config_entry),
    ]

    async_add_entities(entities)


class HomeBrainzSensorEntity(CoordinatorEntity, SensorEntity):
    """Base class for HomeBrainz sensor entities."""

    def __init__(
        self,
        coordinator: HomeBrainzDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.config_entry = config_entry
        self._host = config_entry.data["host"]

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        device_name = "HomeBrainz Clock"
        mac_address = ""
        
        if self.coordinator.data and "status" in self.coordinator.data:
            status = self.coordinator.data["status"]
            device_name = status.get("device", "HomeBrainz Clock")
            mac_address = status.get("mac_address", "")

        return DeviceInfo(
            identifiers={(DOMAIN, mac_address or self._host)},
            name=device_name,
            manufacturer=MANUFACTURER,
            model=MODEL,
            sw_version=self.coordinator.data.get("status", {}).get("version", "Unknown"),
            configuration_url=f"http://{self._host}",
        )


class HomeBrainzTemperatureSensor(HomeBrainzSensorEntity):
    """Temperature sensor."""

    def __init__(
        self,
        coordinator: HomeBrainzDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_unique_id = f"{config_entry.entry_id}_temperature"
        self._attr_name = "Temperature"
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if self.coordinator.data and "sensors" in self.coordinator.data:
            sensors = self.coordinator.data["sensors"]
            if "aht20" in sensors:
                return sensors["aht20"].get("temperature")
        return None


class HomeBrainzHumiditySensor(HomeBrainzSensorEntity):
    """Humidity sensor."""

    def __init__(
        self,
        coordinator: HomeBrainzDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_unique_id = f"{config_entry.entry_id}_humidity"
        self._attr_name = "Humidity"
        self._attr_device_class = SensorDeviceClass.HUMIDITY
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = PERCENTAGE

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if self.coordinator.data and "sensors" in self.coordinator.data:
            sensors = self.coordinator.data["sensors"]
            if "aht20" in sensors:
                return sensors["aht20"].get("humidity")
        return None


class HomeBrainzPressureSensor(HomeBrainzSensorEntity):
    """Pressure sensor."""

    def __init__(
        self,
        coordinator: HomeBrainzDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_unique_id = f"{config_entry.entry_id}_pressure"
        self._attr_name = "Pressure"
        self._attr_device_class = SensorDeviceClass.ATMOSPHERIC_PRESSURE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = UnitOfPressure.HPA

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if self.coordinator.data and "sensors" in self.coordinator.data:
            sensors = self.coordinator.data["sensors"]
            if "bmp280" in sensors:
                return sensors["bmp280"].get("pressure")
        return None


class HomeBrainzAQISensor(HomeBrainzSensorEntity):
    """Air Quality Index sensor."""

    def __init__(
        self,
        coordinator: HomeBrainzDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_unique_id = f"{config_entry.entry_id}_aqi"
        self._attr_name = "Air Quality Index"
        self._attr_device_class = SensorDeviceClass.AQI
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> int | None:
        """Return the state of the sensor."""
        if self.coordinator.data and "sensors" in self.coordinator.data:
            sensors = self.coordinator.data["sensors"]
            if "ens160" in sensors:
                return sensors["ens160"].get("aqi")
        return None


class HomeBrainzCO2Sensor(HomeBrainzSensorEntity):
    """CO2 sensor."""

    def __init__(
        self,
        coordinator: HomeBrainzDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_unique_id = f"{config_entry.entry_id}_co2"
        self._attr_name = "CO2"
        self._attr_device_class = SensorDeviceClass.CO2
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = "ppm"

    @property
    def native_value(self) -> int | None:
        """Return the state of the sensor."""
        if self.coordinator.data and "sensors" in self.coordinator.data:
            sensors = self.coordinator.data["sensors"]
            if "ens160" in sensors:
                return sensors["ens160"].get("co2")
        return None


class HomeBrainzTVOCSensor(HomeBrainzSensorEntity):
    """TVOC sensor."""

    def __init__(
        self,
        coordinator: HomeBrainzDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_unique_id = f"{config_entry.entry_id}_tvoc"
        self._attr_name = "TVOC"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = "ppb"

    @property
    def native_value(self) -> int | None:
        """Return the state of the sensor."""
        if self.coordinator.data and "sensors" in self.coordinator.data:
            sensors = self.coordinator.data["sensors"]
            if "ens160" in sensors:
                return sensors["ens160"].get("tvoc")
        return None


class HomeBrainzWiFiSignalSensor(HomeBrainzSensorEntity):
    """WiFi Signal sensor."""

    def __init__(
        self,
        coordinator: HomeBrainzDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_unique_id = f"{config_entry.entry_id}_wifi_signal"
        self._attr_name = "WiFi Signal"
        self._attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = SIGNAL_STRENGTH_DECIBELS_MILLIWATT

    @property
    def native_value(self) -> int | None:
        """Return the state of the sensor."""
        if self.coordinator.data and "status" in self.coordinator.data:
            status = self.coordinator.data["status"]
            return status.get("rssi")
        return None