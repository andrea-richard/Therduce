"""
Actuator Control Module

Manages GPIO-based control of cooling system actuators including:
- Water pump for evaporative cooling
- Vapor compression chiller
- Dehumidifier unit

Includes safety interlocks, cycle time management, and state tracking.
"""

import time
import logging
from typing import Dict
from enum import Enum

try:
    import RPi.GPIO as GPIO
except ImportError:
    # Mock GPIO for development on non-Pi systems
    GPIO = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ActuatorState(Enum):
    """Actuator operating states"""
    OFF = 0
    ON = 1
    FAULT = 2


class ActuatorError(Exception):
    """Custom exception for actuator-related errors"""
    pass


class Actuator:
    """
    Base class for a single actuator with safety features.
    """
    
    def __init__(self, name: str, gpio_pin: int, min_cycle_time: float = 10.0,
                 max_runtime: float = 600.0, active_low: bool = True):
        """
        Initialize an actuator.
        
        Args:
            name: Human-readable name for the actuator
            gpio_pin: GPIO pin number (BCM numbering)
            min_cycle_time: Minimum seconds between state changes
            max_runtime: Maximum continuous runtime in seconds
            active_low: If True, LOW signal activates relay (safer default)
        """
        self.name = name
        self.gpio_pin = gpio_pin
        self.min_cycle_time = min_cycle_time
        self.max_runtime = max_runtime
        self.active_low = active_low
        
        self.state = ActuatorState.OFF
        self.last_state_change = 0
        self.runtime_start = None
        self.total_runtime = 0.0
        self.cycle_count = 0
        
        logger.info(f"Initialized actuator '{name}' on GPIO {gpio_pin}")
    
    def can_change_state(self) -> bool:
        """
        Check if enough time has passed since last state change.
        
        Returns:
            True if state can be changed
        """
        elapsed = time.time() - self.last_state_change
        return elapsed >= self.min_cycle_time
    
    def is_runtime_exceeded(self) -> bool:
        """
        Check if maximum runtime has been exceeded.
        
        Returns:
            True if actuator has been on too long
        """
        if self.state == ActuatorState.ON and self.runtime_start:
            runtime = time.time() - self.runtime_start
            return runtime >= self.max_runtime
        return False
    
    def turn_on(self) -> bool:
        """
        Turn the actuator on.
        
        Returns:
            True if successful, False if prevented by safety checks
        """
        if self.state == ActuatorState.ON:
            return True  # Already on
        
        if not self.can_change_state():
            logger.warning(f"{self.name}: Cannot turn on - minimum cycle time not met")
            return False
        
        self.state = ActuatorState.ON
        self.last_state_change = time.time()
        self.runtime_start = time.time()
        self.cycle_count += 1
        
        logger.info(f"{self.name}: Turned ON")
        return True
    
    def turn_off(self) -> bool:
        """
        Turn the actuator off.
        
        Returns:
            True if successful
        """
        if self.state == ActuatorState.OFF:
            return True  # Already off
        
        if self.state == ActuatorState.ON and self.runtime_start:
            runtime = time.time() - self.runtime_start
            self.total_runtime += runtime
            logger.debug(f"{self.name}: Runtime was {runtime:.1f}s (total: {self.total_runtime:.1f}s)")
        
        self.state = ActuatorState.OFF
        self.last_state_change = time.time()
        self.runtime_start = None
        
        logger.info(f"{self.name}: Turned OFF")
        return True
    
    def emergency_stop(self):
        """Immediately turn off actuator, bypassing safety checks."""
        self.state = ActuatorState.OFF
        self.runtime_start = None
        logger.warning(f"{self.name}: EMERGENCY STOP")
    
    def get_status(self) -> dict:
        """
        Get current actuator status.
        
        Returns:
            Dictionary with status information
        """
        current_runtime = 0.0
        if self.state == ActuatorState.ON and self.runtime_start:
            current_runtime = time.time() - self.runtime_start
        
        return {
            'name': self.name,
            'pin': self.gpio_pin,
            'state': self.state.name,
            'current_runtime': current_runtime,
            'total_runtime': self.total_runtime,
            'cycle_count': self.cycle_count,
            'time_since_change': time.time() - self.last_state_change
        }


class ActuatorController:
    """
    Main controller for all actuators in the climate control system.
    """
    
    def __init__(self, config: dict = None):
        """
        Initialize the actuator controller.
        
        Args:
            config: Configuration dictionary with GPIO pins and parameters
        """
        self.config = config or {}
        self.gpio_config = self.config.get('gpio', {})
        self.actuator_config = self.config.get('actuators', {})
        self.safety_config = self.config.get('safety', {})
        
        self.actuators: Dict[str, Actuator] = {}
        self.gpio_initialized = False
        self.water_level_ok = True
        self.emergency_mode = False
        
        self._initialize_gpio()
        self._setup_actuators()
    
    def _initialize_gpio(self):
        """Initialize GPIO system."""
        if GPIO is None:
            logger.warning("RPi.GPIO not available - running in simulation mode")
            self.gpio_initialized = False
            return
        
        try:
            # Use BCM pin numbering
            GPIO.setmode(GPIO.BCM)
            
            # Disable warnings about pins already in use
            GPIO.setwarnings(False)
            
            self.gpio_initialized = True
            logger.info("GPIO system initialized (BCM mode)")
            
        except Exception as e:
            logger.error(f"Failed to initialize GPIO: {e}")
            raise ActuatorError(f"GPIO initialization failed: {e}")
    
    def _setup_actuators(self):
        """Setup all actuators based on configuration."""
        # Default GPIO pins
        water_pump_pin = self.gpio_config.get('water_pump', 17)
        chiller_pin = self.gpio_config.get('chiller', 27)
        dehumidifier_pin = self.gpio_config.get('dehumidifier', 22)
        
        # Default timing parameters
        min_cycle = self.actuator_config.get('min_cycle_time', 10)
        max_pump_runtime = self.actuator_config.get('max_pump_runtime', 600)
        max_chiller_runtime = self.actuator_config.get('max_chiller_runtime', 1800)
        max_dehumidifier_runtime = self.actuator_config.get('max_dehumidifier_runtime', 1200)
        
        # Create actuators
        self.actuators['pump'] = Actuator(
            name="Water Pump",
            gpio_pin=water_pump_pin,
            min_cycle_time=min_cycle,
            max_runtime=max_pump_runtime
        )
        
        self.actuators['chiller'] = Actuator(
            name="Chiller",
            gpio_pin=chiller_pin,
            min_cycle_time=min_cycle,
            max_runtime=max_chiller_runtime
        )
        
        self.actuators['dehumidifier'] = Actuator(
            name="Dehumidifier",
            gpio_pin=dehumidifier_pin,
            min_cycle_time=min_cycle,
            max_runtime=max_dehumidifier_runtime
        )
        
        # Setup GPIO pins
        if self.gpio_initialized:
            for actuator in self.actuators.values():
                GPIO.setup(actuator.gpio_pin, GPIO.OUT, initial=GPIO.HIGH if actuator.active_low else GPIO.LOW)
                logger.info(f"Configured GPIO {actuator.gpio_pin} for {actuator.name}")
            
            # Setup water level sensor input
            water_level_pin = self.gpio_config.get('water_level_sensor', 23)
            GPIO.setup(water_level_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            logger.info(f"Configured GPIO {water_level_pin} for water level sensor")
    
    def _set_gpio_state(self, actuator: Actuator, state: bool):
        """
        Set the GPIO pin state for an actuator.
        
        Args:
            actuator: The actuator to control
            state: True for ON, False for OFF
        """
        if not self.gpio_initialized:
            logger.debug(f"Simulation: {actuator.name} -> {'ON' if state else 'OFF'}")
            return
        
        # Account for active-low relays
        gpio_value = GPIO.LOW if (state and actuator.active_low) or (not state and not actuator.active_low) else GPIO.HIGH
        
        try:
            GPIO.output(actuator.gpio_pin, gpio_value)
        except Exception as e:
            logger.error(f"Failed to set GPIO {actuator.gpio_pin}: {e}")
            actuator.state = ActuatorState.FAULT
    
    def check_water_level(self) -> bool:
        """
        Check if water reservoir has adequate level.
        
        Returns:
            True if water level is OK
        """
        if not self.gpio_initialized:
            return True  # Simulation mode - assume OK
        
        if not self.safety_config.get('enable_water_level_check', True):
            return True  # Water level check disabled
        
        water_level_pin = self.gpio_config.get('water_level_sensor', 23)
        
        try:
            # Assuming sensor is LOW when water is low (pull-up resistor)
            level_ok = GPIO.input(water_level_pin) == GPIO.HIGH
            self.water_level_ok = level_ok
            
            if not level_ok:
                logger.warning("Low water level detected!")
            
            return level_ok
            
        except Exception as e:
            logger.error(f"Failed to read water level sensor: {e}")
            return False
    
    def set_pump(self, state: bool) -> bool:
        """
        Control water pump.
        
        Args:
            state: True to turn on, False to turn off
            
        Returns:
            True if successful
        """
        actuator = self.actuators['pump']
        
        # Safety check: Don't run pump if water level is low
        if state and not self.check_water_level():
            logger.error("Cannot start pump - low water level")
            return False
        
        if state:
            success = actuator.turn_on()
            if success:
                self._set_gpio_state(actuator, True)
            return success
        else:
            success = actuator.turn_off()
            if success:
                self._set_gpio_state(actuator, False)
            return success
    
    def set_chiller(self, state: bool) -> bool:
        """
        Control vapor compression chiller.
        
        Args:
            state: True to turn on, False to turn off
            
        Returns:
            True if successful
        """
        actuator = self.actuators['chiller']
        
        if state:
            success = actuator.turn_on()
            if success:
                self._set_gpio_state(actuator, True)
            return success
        else:
            success = actuator.turn_off()
            if success:
                self._set_gpio_state(actuator, False)
            return success
    
    def set_dehumidifier(self, state: bool) -> bool:
        """
        Control dehumidifier.
        
        Args:
            state: True to turn on, False to turn off
            
        Returns:
            True if successful
        """
        actuator = self.actuators['dehumidifier']
        
        if state:
            success = actuator.turn_on()
            if success:
                self._set_gpio_state(actuator, True)
            return success
        else:
            success = actuator.turn_off()
            if success:
                self._set_gpio_state(actuator, False)
            return success
    
    def check_safety(self) -> bool:
        """
        Check all safety conditions.
        
        Returns:
            True if all safety checks pass
        """
        all_ok = True
        
        # Check for runtime exceeded
        for name, actuator in self.actuators.items():
            if actuator.is_runtime_exceeded():
                logger.warning(f"{actuator.name} exceeded maximum runtime - forcing off")
                if name == 'pump':
                    self.set_pump(False)
                elif name == 'chiller':
                    self.set_chiller(False)
                elif name == 'dehumidifier':
                    self.set_dehumidifier(False)
                all_ok = False
        
        # Check water level
        if not self.check_water_level():
            # Turn off pump if water is low
            if self.actuators['pump'].state == ActuatorState.ON:
                logger.error("Low water - shutting down pump")
                self.set_pump(False)
            all_ok = False
        
        return all_ok
    
    def emergency_shutdown(self):
        """Emergency shutdown of all actuators."""
        logger.critical("EMERGENCY SHUTDOWN TRIGGERED")
        self.emergency_mode = True
        
        for name, actuator in self.actuators.items():
            actuator.emergency_stop()
            self._set_gpio_state(actuator, False)
    
    def get_status(self) -> dict:
        """
        Get status of all actuators.
        
        Returns:
            Dictionary with status information
        """
        return {
            'emergency_mode': self.emergency_mode,
            'water_level_ok': self.water_level_ok,
            'gpio_initialized': self.gpio_initialized,
            'pump': self.actuators['pump'].get_status(),
            'chiller': self.actuators['chiller'].get_status(),
            'dehumidifier': self.actuators['dehumidifier'].get_status()
        }
    
    def cleanup(self):
        """Clean up GPIO resources."""
        logger.info("Cleaning up actuator controller")
        
        # Turn off all actuators
        for actuator in self.actuators.values():
            actuator.emergency_stop()
            if self.gpio_initialized:
                self._set_gpio_state(actuator, False)
        
        if self.gpio_initialized and GPIO:
            GPIO.cleanup()
            logger.info("GPIO cleanup complete")


# Example usage and testing
if __name__ == "__main__":
    print("Actuator Controller Test")
    print("-" * 40)
    
    try:
        # Create controller
        controller = ActuatorController()
        print(f"Initial status: {controller.get_status()}")
        print()
        
        # Test pump
        print("Testing water pump...")
        controller.set_pump(True)
        time.sleep(3)
        print(f"Pump status: {controller.actuators['pump'].get_status()}")
        controller.set_pump(False)
        time.sleep(1)
        
        # Test chiller
        print("\nTesting chiller...")
        controller.set_chiller(True)
        time.sleep(3)
        controller.set_chiller(False)
        time.sleep(1)
        
        # Test dehumidifier
        print("\nTesting dehumidifier...")
        controller.set_dehumidifier(True)
        time.sleep(3)
        controller.set_dehumidifier(False)
        
        print("\nFinal status:")
        print(controller.get_status())
        
        controller.cleanup()
        
    except ActuatorError as e:
        print(f"Actuator error: {e}")
    except KeyboardInterrupt:
        print("\nTest interrupted")
        controller.cleanup()

