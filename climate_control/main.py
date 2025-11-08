#!/usr/bin/env python3
"""
Main Climate Control System

Integrates all modules to provide intelligent climate control for produce trucks.
Monitors temperature and humidity, makes control decisions, and manages actuators.
"""

import time
import signal
import sys
import logging

# Import system modules
from sensors import SHT35Sensor, SensorError
from actuators import ActuatorController, ActuatorError
from control_engine import HybridControlEngine, CoolingMode
from data_logger import DataLogger
from dashboard import Dashboard
from settings import get_config_dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('climate_control.log')
    ]
)
logger = logging.getLogger(__name__)


class ClimateControlSystem:
    """
    Main system coordinator integrating all components.
    """
    
    def __init__(self):
        """
        Initialize the climate control system.
        Configuration is loaded from settings.py
        """
        logger.info("=" * 60)
        logger.info("Climate Control System - Starting Up")
        logger.info("=" * 60)
        
        self.running = False
        self.config = self._load_config()
        
        # Initialize components
        self.sensor = None
        self.actuator_controller = None
        self.control_engine = None
        self.data_logger = None
        self.dashboard = None
        
        # Performance tracking
        self.start_time = time.time()
        self.loop_count = 0
        self.error_count = 0
        
        # Initialize all components
        self._initialize_components()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("System initialization complete")
    
    def _load_config(self) -> dict:
        """Load configuration from settings.py."""
        try:
            config = get_config_dict()
            logger.info("Configuration loaded from settings.py")
            logger.info(f"Mango storage targets: {config['targets']['temp_target']}°C, {config['targets']['humidity_target']}% RH")
            return config
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            logger.warning("Using default configuration")
            return {}
    
    def _initialize_components(self):
        """Initialize all system components."""
        try:
            # Initialize sensor
            logger.info("Initializing sensor...")
            sensor_config = self.config.get('sensor', {})
            self.sensor = SHT35Sensor(
                i2c_address=sensor_config.get('i2c_address', 0x44),
                i2c_bus=sensor_config.get('i2c_bus', 1)
            )
            logger.info("✓ Sensor initialized")
            
            # Initialize actuator controller
            logger.info("Initializing actuator controller...")
            self.actuator_controller = ActuatorController(config=self.config)
            logger.info("✓ Actuator controller initialized")
            
            # Initialize control engine
            logger.info("Initializing AI control engine...")
            self.control_engine = HybridControlEngine(config=self.config)
            logger.info("✓ Control engine initialized")
            
            # Initialize data logger
            logger.info("Initializing data logger...")
            self.data_logger = DataLogger(config=self.config)
            self.data_logger.log_event('startup', 'Climate control system started', 'INFO')
            logger.info("✓ Data logger initialized")
            
            # Initialize dashboard (if enabled)
            dashboard_config = self.config.get('dashboard', {})
            if dashboard_config.get('enabled', True):
                logger.info("Initializing web dashboard...")
                self.dashboard = Dashboard(
                    config=self.config,
                    data_logger=self.data_logger,
                    control_engine=self.control_engine,
                    actuator_controller=self.actuator_controller,
                    sensor=self.sensor
                )
                logger.info("✓ Dashboard initialized")
            
        except SensorError as e:
            logger.error(f"Sensor initialization failed: {e}")
            raise
        except ActuatorError as e:
            logger.error(f"Actuator initialization failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Component initialization failed: {e}")
            raise
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, initiating shutdown...")
        self.stop()
    
    def _read_sensors(self) -> tuple:
        """
        Read temperature and humidity from sensors.
        
        Returns:
            Tuple of (temperature, humidity) or (None, None) on error
        """
        try:
            temp, humidity = self.sensor.read()
            
            if temp is None or humidity is None:
                logger.warning("Sensor reading failed")
                self.error_count += 1
                return None, None
            
            return temp, humidity
            
        except Exception as e:
            logger.error(f"Error reading sensors: {e}")
            self.error_count += 1
            return None, None
    
    def _make_control_decision(self, temperature: float, humidity: float):
        """
        Make and execute control decision.
        
        Args:
            temperature: Current temperature in Celsius
            humidity: Current humidity in %
        """
        try:
            # Make decision
            decision = self.control_engine.make_decision(temperature, humidity)
            
            # Log decision
            logger.info(f"Decision: {decision.mode.value} - {decision.reason}")
            self.data_logger.log_control_decision(
                mode=decision.mode.value,
                pump=decision.pump,
                chiller=decision.chiller,
                dehumidifier=decision.dehumidifier,
                reason=decision.reason,
                priority=decision.priority
            )
            
            # Check if manual override is active
            if self.dashboard and self.dashboard.manual_override:
                logger.info("Manual override active - skipping automatic control")
                self.control_engine.execute_decision(decision)  # Still track for statistics
                return
            
            # Execute decision on actuators
            if decision.pump != (self.actuator_controller.actuators['pump'].state.name == 'ON'):
                self.actuator_controller.set_pump(decision.pump)
            
            if decision.chiller != (self.actuator_controller.actuators['chiller'].state.name == 'ON'):
                self.actuator_controller.set_chiller(decision.chiller)
            
            if decision.dehumidifier != (self.actuator_controller.actuators['dehumidifier'].state.name == 'ON'):
                self.actuator_controller.set_dehumidifier(decision.dehumidifier)
            
            # Update control engine state
            self.control_engine.execute_decision(decision)
            
        except Exception as e:
            logger.error(f"Error in control decision: {e}")
            self.error_count += 1
    
    def _perform_safety_checks(self):
        """Perform safety checks and take action if needed."""
        try:
            # Check actuator safety
            if not self.actuator_controller.check_safety():
                logger.warning("Actuator safety check failed")
                self.data_logger.log_event('safety', 'Actuator safety check failed', 'WARNING')
            
            # Check for emergency temperature
            temp, _ = self.sensor.read()
            if temp is not None:
                emergency_temp = self.config.get('safety', {}).get('emergency_shutdown_temp', 15.0)
                if temp > emergency_temp:
                    logger.critical(f"EMERGENCY: Temperature {temp}°C exceeds {emergency_temp}°C!")
                    self.data_logger.log_event('emergency', 
                                              f'Emergency temperature: {temp}°C', 
                                              'CRITICAL')
                    # Emergency cooling will be handled by control engine
            
        except Exception as e:
            logger.error(f"Error in safety checks: {e}")
    
    def _log_status(self):
        """Log current system status."""
        try:
            # Get current readings
            temp, humidity = self.sensor.read()
            
            if temp is not None and humidity is not None:
                # Calculate rates of change
                temp_rate = self.control_engine.calculate_rate_of_change(
                    self.control_engine.temp_history
                )
                humidity_rate = self.control_engine.calculate_rate_of_change(
                    self.control_engine.humidity_history
                )
                
                # Log to database
                self.data_logger.log_sensor_reading(
                    temperature=temp,
                    humidity=humidity,
                    temp_rate=temp_rate,
                    humidity_rate=humidity_rate
                )
                
                # Log actuator states
                for name, actuator in self.actuator_controller.actuators.items():
                    status = actuator.get_status()
                    self.data_logger.log_actuator_state(
                        actuator_name=name,
                        state=status['state'],
                        runtime=status['current_runtime'],
                        cycle_count=status['cycle_count']
                    )
            
        except Exception as e:
            logger.error(f"Error logging status: {e}")
    
    def _control_loop_iteration(self):
        """Perform one iteration of the control loop."""
        # Read sensors
        temp, humidity = self._read_sensors()
        
        if temp is None or humidity is None:
            logger.warning("Skipping control iteration due to sensor failure")
            
            # Check sensor timeout
            sensor_timeout = self.config.get('safety', {}).get('sensor_timeout', 30)
            if self.sensor.last_reading_time and \
               (time.time() - self.sensor.last_reading_time) > sensor_timeout:
                logger.error("Sensor timeout - entering safe mode")
                self.actuator_controller.emergency_shutdown()
                self.data_logger.log_event('error', 'Sensor timeout - safe mode', 'ERROR')
            
            return
        
        # Make and execute control decision
        self._make_control_decision(temp, humidity)
        
        # Perform safety checks
        self._perform_safety_checks()
        
        # Log status
        self._log_status()
        
        # Increment loop counter
        self.loop_count += 1
        
        # Periodic status report
        if self.loop_count % 100 == 0:
            uptime = time.time() - self.start_time
            logger.info(f"Status: {self.loop_count} loops, {uptime/3600:.1f}h uptime, "
                       f"{self.error_count} errors, mode={self.control_engine.current_mode.value}")
            
            # Database maintenance
            db_size = self.data_logger.check_database_size()
            max_size = self.config.get('logging', {}).get('max_db_size_mb', 100)
            if db_size > max_size:
                logger.info(f"Database size {db_size:.1f}MB exceeds limit, cleaning up...")
                self.data_logger.cleanup_old_data(days=7)
    
    def run(self):
        """Main control loop."""
        logger.info("Starting main control loop")
        logger.info("Press Ctrl+C to stop")
        
        self.running = True
        
        # Start dashboard in background if enabled
        if self.dashboard:
            self.dashboard.run_background()
            dashboard_config = self.config.get('dashboard', {})
            logger.info(f"Dashboard available at http://{dashboard_config.get('host', '0.0.0.0')}:"
                       f"{dashboard_config.get('port', 5000)}")
        
        # Main loop
        sensor_config = self.config.get('sensor', {})
        read_interval = sensor_config.get('read_interval', 2.0)
        
        try:
            while self.running:
                loop_start = time.time()
                
                # Perform control loop iteration
                self._control_loop_iteration()
                
                # Sleep for remaining time to maintain interval
                elapsed = time.time() - loop_start
                sleep_time = max(0, read_interval - elapsed)
                
                if sleep_time > 0:
                    time.sleep(sleep_time)
                else:
                    logger.warning(f"Control loop took {elapsed:.2f}s, "
                                 f"exceeding interval of {read_interval}s")
        
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        except Exception as e:
            logger.critical(f"Fatal error in control loop: {e}", exc_info=True)
            self.data_logger.log_event('critical', f'Fatal error: {e}', 'CRITICAL')
        finally:
            self.stop()
    
    def stop(self):
        """Stop the system gracefully."""
        if not self.running:
            return
        
        logger.info("Shutting down climate control system...")
        self.running = False
        
        try:
            # Log shutdown event
            if self.data_logger:
                self.data_logger.log_event('shutdown', 'System shutdown initiated', 'INFO')
            
            # Turn off all actuators
            if self.actuator_controller:
                logger.info("Shutting down actuators...")
                self.actuator_controller.cleanup()
            
            # Close sensor
            if self.sensor:
                logger.info("Closing sensor connection...")
                self.sensor.close()
            
            # Close data logger
            if self.data_logger:
                logger.info("Closing database...")
                self.data_logger.close()
            
            # Print final statistics
            uptime = time.time() - self.start_time
            logger.info("=" * 60)
            logger.info("Shutdown complete")
            logger.info(f"Total runtime: {uptime/3600:.2f} hours")
            logger.info(f"Total iterations: {self.loop_count}")
            logger.info(f"Total errors: {self.error_count}")
            
            if self.control_engine:
                stats = self.control_engine.get_statistics()
                logger.info(f"Control decisions made: {stats['decisions_made']}")
            
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


def main():
    """Main entry point."""
    print("""
    ╔════════════════════════════════════════════════════════╗
    ║     Climate Control System for Produce Trucks         ║
    ║     Post-Harvest Food Loss Prevention                 ║
    ║                                                        ║
    ║     Tata-Cornell Food Challenge - MIT Hackathon       ║
    ╚════════════════════════════════════════════════════════╝
    """)
    
    try:
        # Create and run system
        system = ClimateControlSystem()
        system.run()
        
    except KeyboardInterrupt:
        logger.info("Startup interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Failed to start system: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

