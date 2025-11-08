# Climate Control System for Produce Trucks

A low-cost, intelligent climate control system designed to prevent post-harvest food spoilage during transit in developing countries. This system retrofits into existing un-insulated produce trucks using evaporative cooling, vapor compression chilling, and dehumidification.

## Overview

This system addresses the food loss and waste challenge by maintaining optimal temperature and humidity conditions for perishable produce during transportation. It uses:

- **SHT35-DIS-B sensors** for accurate temperature and humidity monitoring
- **Raspberry Pi Compute Module 5** for intelligent control
- **Hybrid AI decision-making** combining rule-based thresholds with predictive logic
- **Multiple cooling strategies** optimized for energy efficiency

## Hardware Requirements

### Controller
- Raspberry Pi Compute Module 5 (or any Raspberry Pi with GPIO and I2C)

### Sensors
- SHT35-DIS-B Temperature & Humidity Sensor (I2C)

### Actuators
- Water pump (12V DC) with spray nozzles
- Vapor compression chiller unit
- Dehumidifier unit
- 3x Relay modules (for controlling actuators)
- Water reservoir with level sensor
- Water filter (passive)

### Wiring
- GPIO 17: Water pump relay
- GPIO 27: Chiller compressor relay
- GPIO 22: Dehumidifier relay
- GPIO 23: Low water level indicator (input)
- I2C (GPIO 2/3): SHT35-DIS-B sensor

## Installation

### 1. Prepare Raspberry Pi

```bash
# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Enable I2C
sudo raspi-config
# Navigate to: Interface Options -> I2C -> Enable

# Install Python 3 and pip
sudo apt-get install python3 python3-pip python3-venv -y

# Install system dependencies
sudo apt-get install python3-dev libatlas-base-dev -y
```

### 2. Clone and Setup Project

```bash
cd /home/pi
git clone <your-repository-url>
cd climate_control

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### 3. Configure System

Edit `config.yaml` to match your hardware setup and target conditions:

```bash
nano config.yaml
```

Key settings to adjust:
- `sensor.i2c_address`: Your SHT35-DIS-B address (usually 0x44 or 0x45)
- `targets`: Temperature and humidity ranges for your produce
- `gpio`: Pin assignments if different from defaults

### 4. Test Hardware

```bash
# Test sensor connection
python3 -c "from sensors import SHT35Sensor; s = SHT35Sensor(); print(s.read())"

# Test GPIO (will initialize pins)
python3 -c "from actuators import ActuatorController; a = ActuatorController(); print('GPIO initialized')"
```

## Usage

### Running the System

```bash
# Activate virtual environment
source venv/bin/activate

# Run the climate control system
sudo python3 main.py
```

**Note**: `sudo` is required for GPIO access on Raspberry Pi.

### Accessing the Dashboard

Once running, open a web browser and navigate to:
```
http://raspberrypi.local:5000
```

Or use the Pi's IP address:
```
http://192.168.1.XXX:5000
```

The dashboard provides:
- Real-time temperature and humidity readings
- Historical data charts
- Current actuator states
- Manual override controls
- System status and alerts

### Running as a Service (Auto-start on boot)

Create a systemd service:

```bash
sudo nano /etc/systemd/system/climate-control.service
```

Add this content:

```ini
[Unit]
Description=Climate Control System
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/climate_control
ExecStart=/home/pi/climate_control/venv/bin/python3 /home/pi/climate_control/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable climate-control.service
sudo systemctl start climate-control.service

# Check status
sudo systemctl status climate-control.service

# View logs
sudo journalctl -u climate-control.service -f
```

## System Architecture

### Control Logic

The system uses a **hybrid AI approach**:

1. **Rule-Based Control**: Safe operating bounds ensure temperature and humidity stay within acceptable ranges
2. **Predictive Logic**: Monitors rate of change to anticipate problems before thresholds are breached
3. **Energy Optimization**: Prefers evaporative cooling over energy-intensive chilling when possible
4. **Coordinated Control**: Balances cooling and dehumidification to avoid conflicting actions

### Cooling Strategies

1. **Evaporative Cooling** (Most efficient)
   - Activated when temperature rises but humidity is acceptable
   - Sprays cold water from chilled reservoir
   - Energy cost: ~50W (pump + occasional chiller)

2. **Vapor Compression Chilling** (High cooling power)
   - Activated when temperature is critically high
   - Chills the water reservoir for more effective cooling
   - Energy cost: ~500-800W

3. **Dehumidification** (Humidity control)
   - Activated when humidity exceeds targets
   - Removes warm vapor from air
   - Often run in coordination with cooling

### Safety Features

- **Sensor failure detection**: Falls back to safe mode if sensor unresponsive
- **Water level monitoring**: Prevents pump from running dry
- **Actuator timeout protection**: Prevents continuous operation
- **Emergency shutdown**: Triggers at critical temperature thresholds
- **Manual override**: Allows operator intervention via dashboard

## Data Export

Export logged data for analysis:

```bash
# Export to CSV
python3 -c "from data_logger import DataLogger; DataLogger().export_to_csv('my_export.csv')"
```

CSV files are saved to the `exports/` directory and include:
- Timestamp
- Temperature readings
- Humidity readings
- Actuator states (pump, chiller, dehumidifier)
- Control decisions and reasons

## Troubleshooting

### Sensor Not Found

```bash
# Check I2C devices
sudo i2cdetect -y 1

# Should show device at 0x44 or 0x45
```

### GPIO Permission Errors

Run with `sudo` or add user to gpio group:

```bash
sudo usermod -a -G gpio pi
# Logout and login again
```

### Dashboard Not Accessible

Check firewall settings:

```bash
sudo ufw allow 5000
```

### High CPU Usage

Increase sensor read interval in `config.yaml`:

```yaml
sensor:
  read_interval: 5.0  # Increase from 2.0 to 5.0 seconds
```

## Customization

### Adding Produce Type Presets

Edit `config.yaml` and add to the `presets` section:

```yaml
presets:
  my_produce:
    temp_target: 6.0
    humidity_target: 88.0
```

These presets can be selected from the dashboard.

### Tuning Control Parameters

Adjust these in `config.yaml`:

- `control.temp_hysteresis`: Increase to reduce actuator cycling
- `control.prediction_window`: Increase for more anticipatory control
- `actuators.min_cycle_time`: Increase to protect relay lifespan

## Technical Specifications

- **Operating Temperature Range**: 0°C to 40°C
- **Control Accuracy**: ±0.5°C, ±2% RH
- **Response Time**: < 30 seconds
- **Power Consumption**: 5W idle, 50-800W active (depending on cooling mode)
- **Data Logging Rate**: Configurable, default 5 seconds
- **Network Protocol**: HTTP/WebSocket

## Contributing

This project was developed for the MIT hackathon addressing the Food Loss and Waste challenge. Contributions are welcome!

## License

MIT License - Feel free to use and modify for your needs.

## Acknowledgments

- Tata-Cornell Institute for Agriculture and Nutrition for the challenge statement
- MIT D-Lab for evaporative cooling research
- Open source community for excellent Python libraries

## Contact

For questions or support, please open an issue on the project repository.

