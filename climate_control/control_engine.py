"""
Hybrid AI Control Engine

Implements intelligent climate control using a combination of:
1. Rule-based control with safe operating bounds
2. Predictive logic based on trend detection
3. Multi-objective optimization (temperature, humidity, energy)

The engine coordinates evaporative cooling, chilling, and dehumidification
to maintain optimal conditions while minimizing energy consumption.
"""

import time
import logging
from typing import List, Tuple, Optional
from enum import Enum
from collections import deque
import statistics

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CoolingMode(Enum):
    """Operating modes for the cooling system"""
    IDLE = "idle"
    EVAPORATIVE = "evaporative"  # Pump only
    CHILLER = "chiller"  # Chiller + pump
    DEHUMIDIFY = "dehumidify"  # Dehumidifier only
    COOL_AND_DEHUMIDIFY = "cool_and_dehumidify"  # Chiller + dehumidifier
    EMERGENCY = "emergency"  # Emergency cooling


class ControlDecision:
    """Represents a control decision with reasoning"""
    
    def __init__(self, mode: CoolingMode, pump: bool, chiller: bool, dehumidifier: bool, 
                 reason: str, priority: int = 5):
        self.mode = mode
        self.pump = pump
        self.chiller = chiller
        self.dehumidifier = dehumidifier
        self.reason = reason
        self.priority = priority
        self.timestamp = time.time()
    
    def __repr__(self):
        return f"ControlDecision({self.mode.value}, reason='{self.reason}', priority={self.priority})"


class SensorReading:
    """Container for a sensor reading with timestamp"""
    
    def __init__(self, temperature: float, humidity: float, timestamp: float = None):
        self.temperature = temperature
        self.humidity = humidity
        self.timestamp = timestamp or time.time()


class HybridControlEngine:
    """
    Hybrid AI control engine combining rule-based and predictive control.
    """
    
    def __init__(self, config: dict = None):
        """
        Initialize the control engine.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.targets = self.config.get('targets', {})
        self.control_params = self.config.get('control', {})
        self.actuator_params = self.config.get('actuators', {})
        self.safety_params = self.config.get('safety', {})
        
        # Target ranges
        self.temp_target = self.targets.get('temp_target', 5.0)
        self.temp_min = self.targets.get('temp_min', 2.0)
        self.temp_max = self.targets.get('temp_max', 8.0)
        
        self.humidity_target = self.targets.get('humidity_target', 90.0)
        self.humidity_min = self.targets.get('humidity_min', 85.0)
        self.humidity_max = self.targets.get('humidity_max', 95.0)
        
        # Hysteresis for preventing oscillation
        self.temp_hysteresis = self.control_params.get('temp_hysteresis', 0.5)
        self.humidity_hysteresis = self.control_params.get('humidity_hysteresis', 2.0)
        
        # Rate of change thresholds
        self.temp_rate_warning = self.targets.get('temp_rate_warning', 0.5)  # °C/min
        self.humidity_rate_warning = self.targets.get('humidity_rate_warning', 2.0)  # %/min
        
        # History for predictive control
        max_history = self.control_params.get('history_samples', 20)
        self.temp_history: deque = deque(maxlen=max_history)
        self.humidity_history: deque = deque(maxlen=max_history)
        self.reading_history: deque = deque(maxlen=max_history)
        
        # Current state
        self.current_mode = CoolingMode.IDLE
        self.last_decision = None
        self.last_mode_change = time.time()
        self.spray_last_activated = 0
        
        # Statistics
        self.decisions_made = 0
        self.mode_durations = {mode: 0.0 for mode in CoolingMode}
        
        logger.info("Hybrid AI Control Engine initialized")
        logger.info(f"Temperature target: {self.temp_target}°C (range: {self.temp_min}-{self.temp_max}°C)")
        logger.info(f"Humidity target: {self.humidity_target}% (range: {self.humidity_min}-{self.humidity_max}%)")
    
    def add_reading(self, temperature: float, humidity: float):
        """
        Add a new sensor reading to history.
        
        Args:
            temperature: Temperature in Celsius
            humidity: Humidity in %
        """
        reading = SensorReading(temperature, humidity)
        self.reading_history.append(reading)
        self.temp_history.append(temperature)
        self.humidity_history.append(humidity)
    
    def calculate_rate_of_change(self, values: deque, time_window: float = 60.0) -> Optional[float]:
        """
        Calculate rate of change over a time window.
        
        Args:
            values: Deque of values
            time_window: Time window in seconds
            
        Returns:
            Rate of change per minute, or None if insufficient data
        """
        if len(values) < 2:
            return None
        
        # Get values within time window
        current_time = time.time()
        recent_readings = []
        
        for i, reading in enumerate(reversed(self.reading_history)):
            age = current_time - reading.timestamp
            if age <= time_window:
                recent_readings.append((reading.timestamp, list(values)[-(i+1)]))
            else:
                break
        
        if len(recent_readings) < 2:
            return None
        
        # Linear regression for rate of change
        times = [r[0] for r in recent_readings]
        vals = [r[1] for r in recent_readings]
        
        time_range = max(times) - min(times)
        if time_range < 1.0:  # Less than 1 second of data
            return None
        
        # Simple slope calculation
        value_change = vals[-1] - vals[0]
        rate_per_second = value_change / time_range
        rate_per_minute = rate_per_second * 60.0
        
        return rate_per_minute
    
    def predict_future_value(self, current: float, rate: Optional[float], 
                            minutes_ahead: float = 5.0) -> float:
        """
        Predict future value based on current rate of change.
        
        Args:
            current: Current value
            rate: Rate of change per minute
            minutes_ahead: How far ahead to predict
            
        Returns:
            Predicted value
        """
        if rate is None:
            return current
        
        return current + (rate * minutes_ahead)
    
    def calculate_temp_error(self, temperature: float) -> float:
        """Calculate temperature error from target (with hysteresis)"""
        error = temperature - self.temp_target
        
        # Apply hysteresis
        if abs(error) < self.temp_hysteresis:
            return 0.0
        
        return error
    
    def calculate_humidity_error(self, humidity: float) -> float:
        """Calculate humidity error from target (with hysteresis)"""
        error = humidity - self.humidity_target
        
        # Apply hysteresis
        if abs(error) < self.humidity_hysteresis:
            return 0.0
        
        return error
    
    def assess_temperature(self, temperature: float, temp_rate: Optional[float]) -> Tuple[str, int]:
        """
        Assess temperature situation.
        
        Returns:
            Tuple of (assessment string, urgency level 0-10)
        """
        # Check current temperature
        if temperature > self.temp_max + 2:
            return "critically high", 10
        elif temperature > self.temp_max:
            return "high", 8
        elif temperature > self.temp_target + self.temp_hysteresis:
            return "above target", 6
        elif temperature < self.temp_min:
            return "critically low", 9
        elif temperature < self.temp_target - self.temp_hysteresis:
            return "below target", 3
        
        # Check rate of change (predictive)
        if temp_rate is not None and abs(temp_rate) > self.temp_rate_warning:
            prediction_window = self.control_params.get('prediction_window', 5)
            future_temp = self.predict_future_value(temperature, temp_rate, prediction_window)
            
            if future_temp > self.temp_max:
                return f"rising rapidly (predicted {future_temp:.1f}°C)", 7
            elif future_temp < self.temp_min:
                return f"falling rapidly (predicted {future_temp:.1f}°C)", 4
        
        return "optimal", 0
    
    def assess_humidity(self, humidity: float, humidity_rate: Optional[float]) -> Tuple[str, int]:
        """
        Assess humidity situation.
        
        Returns:
            Tuple of (assessment string, urgency level 0-10)
        """
        # Check current humidity
        if humidity > self.humidity_max + 5:
            return "critically high", 9
        elif humidity > self.humidity_max:
            return "high", 7
        elif humidity > self.humidity_target + self.humidity_hysteresis:
            return "above target", 5
        elif humidity < self.humidity_min:
            return "critically low", 8
        elif humidity < self.humidity_target - self.humidity_hysteresis:
            return "below target", 4
        
        # Check rate of change (predictive)
        if humidity_rate is not None and abs(humidity_rate) > self.humidity_rate_warning:
            prediction_window = self.control_params.get('prediction_window', 5)
            future_humidity = self.predict_future_value(humidity, humidity_rate, prediction_window)
            
            if future_humidity > self.humidity_max:
                return f"rising rapidly (predicted {future_humidity:.1f}%)", 6
            elif future_humidity < self.humidity_min:
                return f"falling rapidly (predicted {future_humidity:.1f}%)", 5
        
        return "optimal", 0
    
    def can_spray_now(self) -> bool:
        """Check if enough time has passed since last spray cycle."""
        spray_cooldown = self.actuator_params.get('spray_cooldown', 30)
        elapsed = time.time() - self.spray_last_activated
        return elapsed >= spray_cooldown
    
    def make_decision(self, temperature: float, humidity: float) -> ControlDecision:
        """
        Make a control decision based on current conditions.
        
        This is the main AI decision-making function combining:
        - Rule-based control for safety and bounds
        - Predictive control based on trends
        - Multi-objective optimization
        
        Args:
            temperature: Current temperature in Celsius
            humidity: Current humidity in %
            
        Returns:
            ControlDecision object
        """
        # Add reading to history
        self.add_reading(temperature, humidity)
        
        # Calculate rates of change
        temp_rate = self.calculate_rate_of_change(self.temp_history)
        humidity_rate = self.calculate_rate_of_change(self.humidity_history)
        
        # Assess situation
        temp_assessment, temp_urgency = self.assess_temperature(temperature, temp_rate)
        humidity_assessment, humidity_urgency = self.assess_humidity(humidity, humidity_rate)
        
        logger.debug(f"Temp: {temperature:.1f}°C ({temp_assessment}, urgency={temp_urgency})")
        logger.debug(f"Humidity: {humidity:.1f}% ({humidity_assessment}, urgency={humidity_urgency})")
        
        # Get priorities from config
        priority_temp = self.control_params.get('priority_temperature', 10)
        priority_humidity = self.control_params.get('priority_humidity', 7)
        priority_energy = self.control_params.get('priority_energy', 3)
        
        # Calculate weighted urgencies
        temp_score = temp_urgency * priority_temp / 10
        humidity_score = humidity_urgency * priority_humidity / 10
        
        # Emergency conditions
        emergency_temp = self.safety_params.get('emergency_shutdown_temp', 15.0)
        if temperature > emergency_temp:
            return ControlDecision(
                mode=CoolingMode.EMERGENCY,
                pump=True,
                chiller=True,
                dehumidifier=False,
                reason=f"Emergency: temperature {temperature:.1f}°C exceeds {emergency_temp}°C",
                priority=10
            )
        
        # Decision logic based on combined assessment
        
        # Case 1: Temperature critically high - maximum cooling
        if temp_urgency >= 8:
            if humidity < self.humidity_max:
                # Can use evaporative cooling (adds humidity)
                return ControlDecision(
                    mode=CoolingMode.CHILLER,
                    pump=True,
                    chiller=True,
                    dehumidifier=False,
                    reason=f"Temperature {temp_assessment} - aggressive cooling with chiller",
                    priority=temp_urgency
                )
            else:
                # Must use chiller + dehumidifier
                return ControlDecision(
                    mode=CoolingMode.COOL_AND_DEHUMIDIFY,
                    pump=False,
                    chiller=True,
                    dehumidifier=True,
                    reason=f"Temperature {temp_assessment}, humidity {humidity_assessment} - chiller + dehumidifier",
                    priority=max(temp_urgency, humidity_urgency)
                )
        
        # Case 2: Humidity critically high - dehumidify
        if humidity_urgency >= 7:
            if temp_urgency > 3:
                # Both temp and humidity issues - coordinated response
                return ControlDecision(
                    mode=CoolingMode.COOL_AND_DEHUMIDIFY,
                    pump=False,
                    chiller=True,
                    dehumidifier=True,
                    reason=f"Temperature {temp_assessment}, humidity {humidity_assessment}",
                    priority=max(temp_urgency, humidity_urgency)
                )
            else:
                # Just humidity issue
                return ControlDecision(
                    mode=CoolingMode.DEHUMIDIFY,
                    pump=False,
                    chiller=False,
                    dehumidifier=True,
                    reason=f"Humidity {humidity_assessment} - dehumidifying",
                    priority=humidity_urgency
                )
        
        # Case 3: Moderate temperature increase - prefer evaporative cooling (energy efficient)
        if temp_urgency >= 4 and humidity < self.humidity_max - 5:
            if self.can_spray_now():
                return ControlDecision(
                    mode=CoolingMode.EVAPORATIVE,
                    pump=True,
                    chiller=False,
                    dehumidifier=False,
                    reason=f"Temperature {temp_assessment} - energy-efficient evaporative cooling",
                    priority=temp_urgency
                )
        
        # Case 4: Both slightly off but manageable - use chiller conservatively
        if temp_urgency >= 3 and humidity_urgency >= 3:
            return ControlDecision(
                mode=CoolingMode.CHILLER,
                pump=True,
                chiller=True,
                dehumidifier=False,
                reason=f"Temperature {temp_assessment}, humidity {humidity_assessment} - moderate cooling",
                priority=max(temp_urgency, humidity_urgency)
            )
        
        # Case 5: Predictive action - anticipate problems
        if temp_rate is not None and temp_rate > self.temp_rate_warning:
            if humidity < self.humidity_max - 3:
                return ControlDecision(
                    mode=CoolingMode.EVAPORATIVE,
                    pump=True,
                    chiller=False,
                    dehumidifier=False,
                    reason=f"Predictive: temperature rising at {temp_rate:.2f}°C/min",
                    priority=5
                )
        
        # Case 6: All good - idle mode
        return ControlDecision(
            mode=CoolingMode.IDLE,
            pump=False,
            chiller=False,
            dehumidifier=False,
            reason=f"Conditions optimal (temp {temp_assessment}, humidity {humidity_assessment})",
            priority=0
        )
    
    def execute_decision(self, decision: ControlDecision):
        """
        Execute a control decision (for tracking purposes).
        
        Args:
            decision: The decision to execute
        """
        # Update mode tracking
        if self.current_mode != decision.mode:
            duration = time.time() - self.last_mode_change
            self.mode_durations[self.current_mode] += duration
            self.last_mode_change = time.time()
            
            logger.info(f"Mode change: {self.current_mode.value} -> {decision.mode.value}")
            logger.info(f"Reason: {decision.reason}")
        
        self.current_mode = decision.mode
        self.last_decision = decision
        self.decisions_made += 1
        
        if decision.pump:
            self.spray_last_activated = time.time()
    
    def set_targets(self, temp_target: float = None, humidity_target: float = None):
        """
        Update target temperature and humidity.
        
        Args:
            temp_target: New temperature target in Celsius
            humidity_target: New humidity target in %
        """
        if temp_target is not None:
            self.temp_target = temp_target
            logger.info(f"Temperature target updated to {temp_target}°C")
        
        if humidity_target is not None:
            self.humidity_target = humidity_target
            logger.info(f"Humidity target updated to {humidity_target}%")
    
    def load_preset(self, preset_name: str):
        """
        Load a produce type preset.
        
        Args:
            preset_name: Name of the preset (e.g., 'leafy_greens', 'berries')
        """
        presets = self.config.get('presets', {})
        
        if preset_name not in presets:
            logger.warning(f"Preset '{preset_name}' not found")
            return False
        
        preset = presets[preset_name]
        self.set_targets(
            temp_target=preset.get('temp_target'),
            humidity_target=preset.get('humidity_target')
        )
        
        logger.info(f"Loaded preset: {preset_name}")
        return True
    
    def get_statistics(self) -> dict:
        """
        Get control engine statistics.
        
        Returns:
            Dictionary with statistics
        """
        total_time = sum(self.mode_durations.values()) + (time.time() - self.last_mode_change)
        
        mode_percentages = {}
        for mode, duration in self.mode_durations.items():
            if mode == self.current_mode:
                duration += time.time() - self.last_mode_change
            percentage = (duration / total_time * 100) if total_time > 0 else 0
            mode_percentages[mode.value] = {
                'duration': duration,
                'percentage': percentage
            }
        
        return {
            'current_mode': self.current_mode.value,
            'decisions_made': self.decisions_made,
            'readings_in_history': len(self.reading_history),
            'mode_statistics': mode_percentages,
            'targets': {
                'temperature': self.temp_target,
                'humidity': self.humidity_target
            }
        }


# Example usage and testing
if __name__ == "__main__":
    print("Hybrid AI Control Engine Test")
    print("-" * 40)
    
    # Create engine with default config
    engine = HybridControlEngine()
    
    # Simulate various scenarios
    scenarios = [
        (5.0, 90.0, "Optimal conditions"),
        (9.0, 88.0, "Temperature high"),
        (10.0, 92.0, "Temperature very high, humidity high"),
        (7.0, 97.0, "Humidity too high"),
        (4.0, 85.0, "Good conditions"),
    ]
    
    for temp, humidity, description in scenarios:
        print(f"\n{description}: {temp}°C, {humidity}%")
        decision = engine.make_decision(temp, humidity)
        engine.execute_decision(decision)
        print(f"  Decision: {decision}")
        print(f"  Actions: Pump={decision.pump}, Chiller={decision.chiller}, Dehumidifier={decision.dehumidifier}")
        time.sleep(1)  # Simulate time passing
    
    print("\n" + "-" * 40)
    print("Statistics:")
    stats = engine.get_statistics()
    print(f"Decisions made: {stats['decisions_made']}")
    print(f"Current mode: {stats['current_mode']}")
    print("\nMode usage:")
    for mode, data in stats['mode_statistics'].items():
        print(f"  {mode}: {data['percentage']:.1f}% ({data['duration']:.1f}s)")

