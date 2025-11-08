"""
Climate Control System Settings
All configuration variables for the mango storage system
"""

# ============================================================================
# MANGO STORAGE TARGET CONDITIONS
# ============================================================================

# Temperature Range: 50-54°F (10-12.2°C)
TARGET_TEMP_MIN = 10.0      # °C (50°F)
TARGET_TEMP = 11.0          # °C (52°F) - optimal target
TARGET_TEMP_MAX = 12.2      # °C (54°F)

# Humidity Range: 85-90% RH
TARGET_HUMIDITY_MIN = 85.0  # % RH
TARGET_HUMIDITY = 87.5      # % RH - optimal target
TARGET_HUMIDITY_MAX = 90.0  # % RH

# Rate of change thresholds for predictive control
TEMP_RATE_WARNING = 0.5     # °C per minute
HUMIDITY_RATE_WARNING = 2.0  # % per minute

# ============================================================================
# SENSOR CONFIGURATION
# ============================================================================

SENSOR_I2C_ADDRESS = 0x44   # SHT35-DIS-B I2C address (0x44 or 0x45)
SENSOR_I2C_BUS = 1          # I2C bus number
SENSOR_READ_INTERVAL = 2.0   # Seconds between sensor readings

# ============================================================================
# GPIO PIN ASSIGNMENTS
# ============================================================================

GPIO_WATER_PUMP = 17
GPIO_CHILLER = 27
GPIO_DEHUMIDIFIER = 22
GPIO_WATER_LEVEL_SENSOR = 23  # Input pin for low water level indicator

# ============================================================================
# ACTUATOR CONTROL PARAMETERS
# ============================================================================

ACTUATOR_MIN_CYCLE_TIME = 10        # Seconds between state changes
ACTUATOR_MAX_PUMP_RUNTIME = 600     # 10 minutes
ACTUATOR_MAX_CHILLER_RUNTIME = 1800  # 30 minutes
ACTUATOR_MAX_DEHUMIDIFIER_RUNTIME = 1200  # 20 minutes
ACTUATOR_SPRAY_DURATION = 5         # Seconds
ACTUATOR_SPRAY_COOLDOWN = 30           # Seconds between spray cycles

# ============================================================================
# CONTROL LOGIC PARAMETERS
# ============================================================================

CONTROL_TEMP_HYSTERESIS = 0.5        # °C - prevents oscillation
CONTROL_HUMIDITY_HYSTERESIS = 2.0    # % - prevents oscillation
CONTROL_PREDICTION_WINDOW = 5        # Minutes ahead to predict
CONTROL_HISTORY_SAMPLES = 20         # Number of readings for trend analysis

# Control priorities (0-10, higher = more important)
CONTROL_PRIORITY_TEMPERATURE = 10
CONTROL_PRIORITY_HUMIDITY = 7
CONTROL_PRIORITY_ENERGY = 3

# ============================================================================
# DATA LOGGING
# ============================================================================

LOGGING_DATABASE_PATH = "climate_data.db"
LOGGING_INTERVAL = 5                 # Seconds between log entries
LOGGING_CSV_EXPORT_DIR = "exports"
LOGGING_MAX_DB_SIZE_MB = 100        # Auto-cleanup when exceeded

# ============================================================================
# DASHBOARD SETTINGS
# ============================================================================

DASHBOARD_ENABLED = True
DASHBOARD_HOST = "0.0.0.0"          # Listen on all interfaces
DASHBOARD_PORT = 5000
DASHBOARD_REFRESH_INTERVAL = 2      # Seconds between auto-refresh
DASHBOARD_CHART_HISTORY_HOURS = 24   # Hours of data to show in charts

# ============================================================================
# SAFETY SETTINGS
# ============================================================================

SAFETY_ENABLE_WATER_LEVEL_CHECK = True
SAFETY_EMERGENCY_SHUTDOWN_TEMP = 15.0  # °C - shutdown if exceeded
SAFETY_SENSOR_TIMEOUT = 30             # Seconds - fallback if sensor unresponsive
SAFETY_ENABLE_MANUAL_OVERRIDE = True

# ============================================================================
# PRODUCE TYPE PRESETS
# ============================================================================

PRESETS = {
    'mango': {
        'temp_target': 11.0,
        'humidity_target': 87.5,
        'description': 'Mango optimal storage: 50-54°F (10-12.2°C), 85-90% RH'
    },
    'leafy_greens': {
        'temp_target': 4.0,
        'humidity_target': 95.0,
        'description': 'Leafy greens storage'
    },
    'berries': {
        'temp_target': 2.0,
        'humidity_target': 90.0,
        'description': 'Berries storage'
    },
    'tomatoes': {
        'temp_target': 13.0,
        'humidity_target': 85.0,
        'description': 'Tomatoes storage'
    },
    'citrus': {
        'temp_target': 8.0,
        'humidity_target': 85.0,
        'description': 'Citrus storage'
    }
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_config_dict():
    """
    Convert all settings to a dictionary format (for backward compatibility).
    This allows the code to work with either settings.py or config.yaml.
    """
    return {
        'sensor': {
            'i2c_address': SENSOR_I2C_ADDRESS,
            'i2c_bus': SENSOR_I2C_BUS,
            'read_interval': SENSOR_READ_INTERVAL
        },
        'targets': {
            'temp_min': TARGET_TEMP_MIN,
            'temp_target': TARGET_TEMP,
            'temp_max': TARGET_TEMP_MAX,
            'humidity_min': TARGET_HUMIDITY_MIN,
            'humidity_target': TARGET_HUMIDITY,
            'humidity_max': TARGET_HUMIDITY_MAX,
            'temp_rate_warning': TEMP_RATE_WARNING,
            'humidity_rate_warning': HUMIDITY_RATE_WARNING
        },
        'gpio': {
            'water_pump': GPIO_WATER_PUMP,
            'chiller': GPIO_CHILLER,
            'dehumidifier': GPIO_DEHUMIDIFIER,
            'water_level_sensor': GPIO_WATER_LEVEL_SENSOR
        },
        'actuators': {
            'min_cycle_time': ACTUATOR_MIN_CYCLE_TIME,
            'max_pump_runtime': ACTUATOR_MAX_PUMP_RUNTIME,
            'max_chiller_runtime': ACTUATOR_MAX_CHILLER_RUNTIME,
            'max_dehumidifier_runtime': ACTUATOR_MAX_DEHUMIDIFIER_RUNTIME,
            'spray_duration': ACTUATOR_SPRAY_DURATION,
            'spray_cooldown': ACTUATOR_SPRAY_COOLDOWN
        },
        'control': {
            'temp_hysteresis': CONTROL_TEMP_HYSTERESIS,
            'humidity_hysteresis': CONTROL_HUMIDITY_HYSTERESIS,
            'prediction_window': CONTROL_PREDICTION_WINDOW,
            'history_samples': CONTROL_HISTORY_SAMPLES,
            'priority_temperature': CONTROL_PRIORITY_TEMPERATURE,
            'priority_humidity': CONTROL_PRIORITY_HUMIDITY,
            'priority_energy': CONTROL_PRIORITY_ENERGY
        },
        'logging': {
            'database_path': LOGGING_DATABASE_PATH,
            'log_interval': LOGGING_INTERVAL,
            'csv_export_dir': LOGGING_CSV_EXPORT_DIR,
            'max_db_size_mb': LOGGING_MAX_DB_SIZE_MB
        },
        'dashboard': {
            'enabled': DASHBOARD_ENABLED,
            'host': DASHBOARD_HOST,
            'port': DASHBOARD_PORT,
            'refresh_interval': DASHBOARD_REFRESH_INTERVAL,
            'chart_history_hours': DASHBOARD_CHART_HISTORY_HOURS
        },
        'safety': {
            'enable_water_level_check': SAFETY_ENABLE_WATER_LEVEL_CHECK,
            'emergency_shutdown_temp': SAFETY_EMERGENCY_SHUTDOWN_TEMP,
            'sensor_timeout': SAFETY_SENSOR_TIMEOUT,
            'enable_manual_override': SAFETY_ENABLE_MANUAL_OVERRIDE
        },
        'presets': PRESETS
    }

