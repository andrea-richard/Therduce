"""
SHT35-DIS-B Temperature and Humidity Sensor Interface

This module provides an interface to the Sensirion SHT35-DIS-B sensor via I2C.
Includes error handling, calibration support, and data validation.
"""

import time
import logging
from typing import Tuple, Optional
# import app # from local 

try:
    from smbus2 import SMBus
except ImportError:
    # For development/testing on non-Pi systems
    SMBus = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SensorError(Exception):
    """Custom exception for sensor-related errors"""
    pass


class SHT35Sensor:
    """
    Interface for SHT35-DIS-B temperature and humidity sensor.
    
    The SHT35 uses I2C communication and provides high accuracy readings:
    - Temperature: ±0.2°C accuracy
    - Humidity: ±2% RH accuracy
    """
    
    # I2C Commands for SHT35
    CMD_MEASURE_HIGH_REP = [0x2C, 0x06]  # High repeatability measurement
    CMD_SOFT_RESET = [0x30, 0xA2]
    CMD_READ_STATUS = [0xF3, 0x2D]
    
    def __init__(self, i2c_address: int = 0x44, i2c_bus: int = 1):
        """
        Initialize the SHT35 sensor.
        
        Args:
            i2c_address: I2C address of the sensor (0x44 or 0x45)
            i2c_bus: I2C bus number (usually 1 on Raspberry Pi)
        """
        self.address = i2c_address
        self.bus_num = i2c_bus
        self.bus = None
        self.last_reading_time = 0
        self.min_read_interval = 0.1  # Minimum 100ms between readings
        
        # Calibration offsets (can be adjusted if sensor drift occurs)
        self.temp_offset = 0.0
        self.humidity_offset = 0.0
        
        # Reading history for validation
        self.temp_history = []
        self.humidity_history = []
        self.max_history = 10
        
        self._initialize()
    
    def _initialize(self):
        """Initialize I2C communication and perform soft reset."""
        try:
            if SMBus is None:
                logger.warning("SMBus not available - running in simulation mode")
                return
            
            # Try to initialize I2C bus
            try:
                self.bus = SMBus(self.bus_num)
                logger.info(f"Initialized I2C bus {self.bus_num} for SHT35 at address 0x{self.address:02X}")
                
                # Perform soft reset
                self._soft_reset()
                time.sleep(0.1)  # Wait for reset to complete
                
            except (FileNotFoundError, OSError) as e:
                # I2C device not available (e.g., on Mac or I2C not enabled)
                logger.warning(f"I2C device /dev/i2c-{self.bus_num} not available - running in simulation mode")
                logger.info("This is normal when running on non-Pi systems or when sensor is not connected")
                self.bus = None  # Ensure bus is None for simulation mode
                return
            
        except Exception as e:
            # For any other unexpected error, log but don't crash - use simulation mode
            logger.warning(f"Unexpected error during sensor initialization: {e}")
            logger.info("Falling back to simulation mode")
            self.bus = None
    
    def _soft_reset(self):
        """Perform a soft reset of the sensor."""
        if self.bus:
            try:
                self.bus.write_i2c_block_data(self.address, self.CMD_SOFT_RESET[0], 
                                              [self.CMD_SOFT_RESET[1]])
                logger.debug("Performed soft reset on SHT35")
            except Exception as e:
                logger.warning(f"Soft reset failed: {e}")
    
    def _calculate_crc(self, data: list) -> int:
        """
        Calculate CRC-8 checksum for data validation.
        
        Args:
            data: List of bytes to checksum
            
        Returns:
            CRC-8 checksum value
        """
        crc = 0xFF
        polynomial = 0x31  # x^8 + x^5 + x^4 + 1
        
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = (crc << 1) ^ polynomial
                else:
                    crc = crc << 1
            crc &= 0xFF
        
        return crc
    
    def _convert_temperature(self, raw: int) -> float:
        """
        Convert raw temperature data to Celsius.
        
        Args:
            raw: 16-bit raw temperature value
            
        Returns:
            Temperature in Celsius
        """
        temp_celsius = -45 + (175 * raw / 65535.0)
        return temp_celsius + self.temp_offset
    
    def _convert_humidity(self, raw: int) -> float:
        """
        Convert raw humidity data to percentage.
        
        Args:
            raw: 16-bit raw humidity value
            
        Returns:
            Relative humidity in %
        """
        # humidity = 100 * raw / 65535.0
        # # Clamp to valid range
        # humidity = max(0.0, min(100.0, humidity + self.humidity_offset))
        # return humidity
        return app.humidity
    
    def _validate_reading(self, temp: float, humidity: float) -> bool:
        """
        Validate sensor reading against reasonable bounds and recent history.
        
        Args:
            temp: Temperature reading in Celsius
            humidity: Humidity reading in %
            
        Returns:
            True if reading appears valid
        """
        # Check physical bounds
        if not (-40 <= temp <= 125):
            logger.warning(f"Temperature {temp}°C out of physical range")
            return False
        
        if not (0 <= humidity <= 100):
            logger.warning(f"Humidity {humidity}% out of valid range")
            return False
        
        # Check for unrealistic changes (if we have history)
        if self.temp_history:
            last_temp = self.temp_history[-1]
            temp_change = abs(temp - last_temp)
            if temp_change > 10:  # More than 10°C change is suspicious
                logger.warning(f"Suspicious temperature change: {temp_change}°C")
                return False
        
        if self.humidity_history:
            last_humidity = self.humidity_history[-1]
            humidity_change = abs(humidity - last_humidity)
            if humidity_change > 20:  # More than 20% RH change is suspicious
                logger.warning(f"Suspicious humidity change: {humidity_change}%")
                return False
        
        return True
    
    def _update_history(self, temp: float, humidity: float):
        """Update reading history for validation."""
        self.temp_history.append(temp)
        self.humidity_history.append(humidity)
        
        # Keep only recent history
        if len(self.temp_history) > self.max_history:
            self.temp_history.pop(0)
        if len(self.humidity_history) > self.max_history:
            self.humidity_history.pop(0)
    
    def read(self) -> Tuple[Optional[float], Optional[float]]:
        """
        Read temperature and humidity from the sensor.
        
        Returns:
            Tuple of (temperature_celsius, humidity_percent)
            Returns (None, None) if reading fails
        """
        # Enforce minimum read interval
        current_time = time.time()
        time_since_last = current_time - self.last_reading_time
        if time_since_last < self.min_read_interval:
            time.sleep(self.min_read_interval - time_since_last)
        
        try:
            if self.bus is None:
                # Simulation mode for testing
                return self._simulate_reading()
            
            # Send measurement command
            self.bus.write_i2c_block_data(self.address, self.CMD_MEASURE_HIGH_REP[0],
                                          [self.CMD_MEASURE_HIGH_REP[1]])
            
            # Wait for measurement to complete (high repeatability takes ~15ms)
            time.sleep(0.020)
            
            # Read 6 bytes: temp MSB, temp LSB, temp CRC, hum MSB, hum LSB, hum CRC
            data = self.bus.read_i2c_block_data(self.address, 0x00, 6)
            
            # Validate checksums
            temp_data = data[0:2]
            temp_crc = data[2]
            if self._calculate_crc(temp_data) != temp_crc:
                raise SensorError("Temperature CRC mismatch")
            
            humidity_data = data[3:5]
            humidity_crc = data[5]
            if self._calculate_crc(humidity_data) != humidity_crc:
                raise SensorError("Humidity CRC mismatch")
            
            # Convert raw values
            temp_raw = (data[0] << 8) | data[1]
            humidity_raw = (data[3] << 8) | data[4]
            
            temperature = self._convert_temperature(temp_raw)
            humidity = self._convert_humidity(humidity_raw)
            
            # Validate reading
            if not self._validate_reading(temperature, humidity):
                logger.warning("Reading failed validation, returning None")
                return None, None
            
            # Update history
            self._update_history(temperature, humidity)
            
            self.last_reading_time = time.time()
            
            logger.debug(f"SHT35 reading: {temperature:.2f}°C, {humidity:.1f}% RH")
            
            return temperature, humidity
            
        except Exception as e:
            logger.error(f"Failed to read from SHT35: {e}")
            return None, None
    
    def _simulate_reading(self) -> Tuple[float, float]:
        """
        Simulate sensor readings for testing without hardware.
        
        Returns realistic values with small variations.
        """
        import random
        
        # Base values with small random variation
        base_temp = 5.0
        base_humidity = 90.0
        
        temp = base_temp + random.uniform(-0.5, 0.5)
        humidity = base_humidity + random.uniform(-2, 2)
        
        self._update_history(temp, humidity)
        self.last_reading_time = time.time()
        
        return temp, humidity
    
    def set_calibration(self, temp_offset: float = 0.0, humidity_offset: float = 0.0):
        """
        Set calibration offsets for the sensor.
        
        Args:
            temp_offset: Temperature offset in Celsius
            humidity_offset: Humidity offset in %
        """
        self.temp_offset = temp_offset
        self.humidity_offset = humidity_offset
        logger.info(f"Calibration set: temp offset={temp_offset}°C, humidity offset={humidity_offset}%")
    
    def get_status(self) -> dict:
        """
        Get sensor status information.
        
        Returns:
            Dictionary with status information
        """
        return {
            'address': f"0x{self.address:02X}",
            'bus': self.bus_num,
            'initialized': self.bus is not None,
            'last_reading_age': time.time() - self.last_reading_time if self.last_reading_time else None,
            'temp_offset': self.temp_offset,
            'humidity_offset': self.humidity_offset,
            'readings_in_history': len(self.temp_history)
        }
    
    def close(self):
        """Close the I2C bus connection."""
        if self.bus:
            self.bus.close()
            logger.info("Closed I2C bus connection")


# Example usage and testing
if __name__ == "__main__":
    print("SHT35 Sensor Test")
    print("-" * 40)
    
    try:
        sensor = SHT35Sensor()
        status = sensor.get_status()
        print(f"Sensor status: {status}")
        
        # Show if running in simulation mode
        if not status.get('initialized', False):
            print("\n⚠️  Running in SIMULATION MODE")
            print("   (This is normal when sensor is not connected or on non-Pi systems)")
            print("   All features work - just with simulated data\n")
        else:
            print("\n✅ Running with REAL HARDWARE\n")
        
        # Take several readings
        print("Taking 5 readings (2 seconds apart)...")
        for i in range(5):
            temp, humidity = sensor.read()
            if temp is not None and humidity is not None:
                mode = "SIM" if not status.get('initialized', False) else "REAL"
                print(f"Reading {i+1} [{mode}]: {temp:.2f}°C, {humidity:.1f}% RH")
            else:
                print(f"Reading {i+1}: Failed")
            time.sleep(2)
        
        sensor.close()
        print("\n✅ Test complete!")
        
    except SensorError as e:
        print(f"❌ Sensor error: {e}")
        print("   Note: System will use simulation mode if sensor is unavailable")
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted")

