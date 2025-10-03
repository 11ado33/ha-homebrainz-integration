## HomeBrainz ESPTimeCast Integration

Connect your HomeBrainz ESPTimeCast device to Home Assistant for comprehensive environmental monitoring.

### Features

- **7 Sensor Types**: Temperature, Humidity, Pressure, Air Quality Index, CO2, TVOC, and WiFi Signal
- **Easy Setup**: Simple configuration through Home Assistant UI
- **Real-time Monitoring**: 30-second update intervals
- **Device Management**: Direct access to device web interface

### Supported Sensors

- **AHT20**: Temperature and Humidity
- **BMP280**: Atmospheric Pressure  
- **ENS160**: Air Quality Index, CO2, and TVOC
- **WiFi**: Signal Strength Monitoring

### Quick Setup

1. Ensure your ESPTimeCast device is connected to your WiFi network
2. Note the device's IP address
3. Add the integration through **Settings** > **Devices & Services** > **Add Integration**
4. Search for "HomeBrainz" and enter your device IP address

The integration will automatically discover all available sensors and create entities in Home Assistant.

### Device Web Interface

Access your device's configuration page directly through the device information panel in Home Assistant, or browse to `http://[device-ip]/` for:

- Real-time sensor readings
- WiFi configuration
- MQTT settings
- Device diagnostics

### Troubleshooting

If you experience connection issues:
- Verify the device IP address
- Ensure Home Assistant and the device are on the same network
- Check that the device's web interface is accessible