"""Constants for the HomeBrainz integration."""

DOMAIN = "homebrainz"

# Device info
MANUFACTURER = "HomeBrainz"
MODEL = "HomeBrainz Clock"

# Default values
DEFAULT_PORT = 80
DEFAULT_SCAN_INTERVAL = 30

# Configuration
CONF_HOST = "host"

# Sensor types
SENSOR_TEMPERATURE = "temperature"
SENSOR_HUMIDITY = "humidity"
SENSOR_PRESSURE = "pressure"
SENSOR_AQI = "aqi"
SENSOR_CO2 = "co2"
SENSOR_TVOC = "tvoc"
SENSOR_WIFI_SIGNAL = "wifi_signal"

# Extended telemetry
SENSOR_GAS_RESISTANCE = "gas_resistance"
SENSOR_TEMPERATURE_OFFSET = "temperature_offset"
SENSOR_HUMIDITY_OFFSET = "humidity_offset"
SENSOR_AQI_RATING = "aqi_rating"
SENSOR_UPTIME = "uptime"
SENSOR_FREE_HEAP = "free_heap"
SENSOR_BRIGHTNESS = "brightness"
SENSOR_DISPLAY_MODE = "display_mode"
SENSOR_WEBSOCKET_CLIENTS = "websocket_clients"
SENSOR_SENSORS_AVAILABLE = "sensors_available"
SENSOR_WEATHER_AVAILABLE = "weather_available"
SENSOR_WEATHER_TEMPERATURE = "weather_temperature"
SENSOR_WEATHER_HUMIDITY = "weather_humidity"
SENSOR_WEATHER_DESCRIPTION = "weather_description"
SENSOR_WIFI_CONNECTED = "wifi_connected"
SENSOR_IP_ADDRESS = "ip_address"
SENSOR_MAC_ADDRESS = "mac_address"
SENSOR_FIRMWARE_VERSION = "firmware_version"