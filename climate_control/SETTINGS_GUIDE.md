# Settings Configuration Guide

## Overview

All configuration variables are now in `settings.py` instead of `config.yaml`. This makes it easier to modify values directly in Python code.

## Quick Reference

### Mango Storage Targets (Current Settings)

```python
# Temperature: 50-54°F (10-12.2°C)
TARGET_TEMP_MIN = 10.0      # 50°F
TARGET_TEMP = 11.0          # 52°F (optimal)
TARGET_TEMP_MAX = 12.2      # 54°F

# Humidity: 85-90% RH
TARGET_HUMIDITY_MIN = 85.0
TARGET_HUMIDITY = 87.5      # Optimal
TARGET_HUMIDITY_MAX = 90.0
```

## How to Modify Settings

### Example: Change Temperature Target

1. Open `settings.py`
2. Find the variable you want to change:
   ```python
   TARGET_TEMP = 11.0  # Change this value
   ```
3. Save the file
4. Restart the system

### Example: Change Humidity Range

```python
# In settings.py:
TARGET_HUMIDITY_MIN = 85.0  # Minimum humidity
TARGET_HUMIDITY = 87.5      # Target humidity
TARGET_HUMIDITY_MAX = 90.0  # Maximum humidity
```

## All Available Settings

### Temperature & Humidity
- `TARGET_TEMP_MIN` - Minimum temperature (°C)
- `TARGET_TEMP` - Target temperature (°C)
- `TARGET_TEMP_MAX` - Maximum temperature (°C)
- `TARGET_HUMIDITY_MIN` - Minimum humidity (%)
- `TARGET_HUMIDITY` - Target humidity (%)
- `TARGET_HUMIDITY_MAX` - Maximum humidity (%)

### Sensor Settings
- `SENSOR_I2C_ADDRESS` - I2C address (0x44 or 0x45)
- `SENSOR_I2C_BUS` - I2C bus number
- `SENSOR_READ_INTERVAL` - Reading interval (seconds)

### GPIO Pins
- `GPIO_WATER_PUMP` - Water pump relay pin
- `GPIO_CHILLER` - Chiller relay pin
- `GPIO_DEHUMIDIFIER` - Dehumidifier relay pin
- `GPIO_WATER_LEVEL_SENSOR` - Water level sensor pin

### Actuator Control
- `ACTUATOR_MIN_CYCLE_TIME` - Minimum time between state changes (seconds)
- `ACTUATOR_MAX_PUMP_RUNTIME` - Max pump runtime (seconds)
- `ACTUATOR_MAX_CHILLER_RUNTIME` - Max chiller runtime (seconds)
- `ACTUATOR_MAX_DEHUMIDIFIER_RUNTIME` - Max dehumidifier runtime (seconds)

### Control Logic
- `CONTROL_TEMP_HYSTERESIS` - Temperature hysteresis (°C)
- `CONTROL_HUMIDITY_HYSTERESIS` - Humidity hysteresis (%)
- `CONTROL_PREDICTION_WINDOW` - Prediction window (minutes)
- `CONTROL_PRIORITY_TEMPERATURE` - Temperature priority (0-10)
- `CONTROL_PRIORITY_HUMIDITY` - Humidity priority (0-10)
- `CONTROL_PRIORITY_ENERGY` - Energy priority (0-10)

### Dashboard
- `DASHBOARD_ENABLED` - Enable/disable dashboard
- `DASHBOARD_HOST` - Host address
- `DASHBOARD_PORT` - Port number
- `DASHBOARD_REFRESH_INTERVAL` - Auto-refresh interval (seconds)

### Safety
- `SAFETY_EMERGENCY_SHUTDOWN_TEMP` - Emergency shutdown temperature (°C)
- `SAFETY_SENSOR_TIMEOUT` - Sensor timeout (seconds)
- `SAFETY_ENABLE_WATER_LEVEL_CHECK` - Enable water level checking

## Using Settings in Code

### Import Individual Variables

```python
from settings import TARGET_TEMP, TARGET_HUMIDITY

print(f"Target: {TARGET_TEMP}°C, {TARGET_HUMIDITY}% RH")
```

### Import All Settings as Dictionary

```python
from settings import get_config_dict

config = get_config_dict()
temp_target = config['targets']['temp_target']
humidity_target = config['targets']['humidity_target']
```

## Temperature Conversion Reference

- **50°F = 10°C**
- **52°F = 11.1°C** (approximately 11°C)
- **54°F = 12.2°C**

Formula: `°C = (°F - 32) × 5/9`

## Presets

Presets are stored in the `PRESETS` dictionary:

```python
PRESETS = {
    'mango': {
        'temp_target': 11.0,
        'humidity_target': 87.5,
        'description': 'Mango optimal storage: 50-54°F (10-12.2°C), 85-90% RH'
    },
    # ... other presets
}
```

To add a new preset, add it to the `PRESETS` dictionary in `settings.py`.

## Notes

- All temperature values are in **Celsius** (°C)
- All humidity values are in **percent** (%)
- Settings take effect immediately after restarting the system
- The old `config.yaml` file is no longer used (but kept for reference)

