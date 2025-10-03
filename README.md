# HomeBrainz Home Assistant Integration

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![hacs][hacsbadge]][hacs]
[![Project Maintenance][maintenance-shield]][user_profile]

**This integration will set up the following platforms.**

Platform | Description
-- | --
`sensor` | Temperature, Humidity, Pressure, Air Quality Index, CO2, TVOC, and WiFi Signal sensors

## Features

- **Multiple Sensor Support**: Monitors temperature, humidity, atmospheric pressure, air quality (AQI), CO2 levels, TVOC (Total Volatile Organic Compounds), and WiFi signal strength
- **Automatic Discovery**: Easy setup through Home Assistant's configuration flow
- **Real-time Updates**: Polls device every 30 seconds for current sensor readings
- **Device Information**: Shows device details including firmware version and MAC address
- **Web Interface**: Direct link to device configuration page

## Supported Devices

- HomeBrainz Clock with sensor package
  - AHT20 Temperature & Humidity Sensor
  - BMP280 Barometric Pressure Sensor  
  - ENS160 Air Quality Sensor (AQI, CO2, TVOC)
  - WiFi Signal Strength Monitoring

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/11ado33/ha-homebrainz-integration`
6. Select "Integration" as the category
7. Click "Add"
8. Find "HomeBrainz" in the integrations list and click "Download"
9. Restart Home Assistant

### Manual Installation

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`)
2. If you do not have a `custom_components` directory (folder) there, you need to create it
3. In the `custom_components` directory (folder) create a new folder called `homebrainz`
4. Download _all_ the files from the `custom_components/homebrainz/` directory (folder) in this repository
5. Place the files you downloaded in the new directory (folder) you created
6. Restart Home Assistant

## Configuration

### Setting up the Integration

1. In Home Assistant, go to **Settings** > **Devices & Services**
2. Click **Add Integration**
3. Search for "HomeBrainz" and select it
4. Enter your HomeBrainz Clock device's IP address (e.g., `192.168.1.207`)
5. Click **Submit**

The integration will automatically discover your device and create all available sensor entities.

### Finding Your Device IP Address

You can find your device's IP address by:
- Checking your WiFi router's connected devices list
- Using a network scanner app
- Connecting to the device's serial console during boot

## Entities

Once configured, the integration will create the following entities:

- `sensor.temperature` - Temperature reading from AHT20 sensor (°C)
- `sensor.humidity` - Humidity reading from AHT20 sensor (%)
- `sensor.pressure` - Atmospheric pressure from BMP280 sensor (hPa)
- `sensor.air_quality_index` - Air quality index from ENS160 sensor (1-5 scale)
- `sensor.co2` - CO2 concentration from ENS160 sensor (ppm)
- `sensor.tvoc` - Total Volatile Organic Compounds from ENS160 sensor (ppb)
- `sensor.wifi_signal` - WiFi signal strength (dBm)

## Device Configuration

Your HomeBrainz Clock device can be configured through its web interface. The integration provides a direct link to the device configuration page in the device information panel.

### Web Interface Features

- Real-time sensor readings
- WiFi configuration
- MQTT settings (for alternative integration methods)
- Device information and diagnostics

## Troubleshooting

### Integration Won't Connect

1. Verify the device IP address is correct
2. Ensure the device is powered on and connected to your network
3. Check that Home Assistant can reach the device (same subnet/VLAN)
4. Verify the device's web interface is accessible by browsing to `http://[device-ip]/`

### Missing Sensors

If some sensors are not appearing:
1. Check the device's `/sensors` endpoint directly: `http://[device-ip]/sensors`
2. Ensure all sensor hardware is properly connected
3. Check device logs through serial console if available

### Update Issues

If the integration stops updating:
1. Check Home Assistant logs for connection errors
2. Verify the device is still accessible
3. Try reloading the integration from **Settings** > **Devices & Services**

## Contributing

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

## Credits

This project was generated from [@oncleben31](https://github.com/oncleben31)'s [Home Assistant Custom Component Cookiecutter](https://github.com/oncleben31/cookiecutter-homeassistant-custom-component) template.

Code template was mainly taken from [@Ludeeus](https://github.com/ludeeus)'s [integration_blueprint][integration_blueprint] template

---

[integration_blueprint]: https://github.com/ludeeus/integration_blueprint
[commits-shield]: https://img.shields.io/github/commit-activity/y/11ado33/ha-homebrainz-integration.svg?style=for-the-badge
[commits]: https://github.com/11ado33/ha-homebrainz-integration/commits/main
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[license-shield]: https://img.shields.io/github/license/11ado33/ha-homebrainz-integration.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-%4011ado33-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/11ado33/ha-homebrainz-integration.svg?style=for-the-badge
[releases]: https://github.com/11ado33/ha-homebrainz-integration/releases
[user_profile]: https://github.com/11ado33