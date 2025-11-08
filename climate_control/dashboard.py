"""
Web Dashboard Module

Flask-based web interface for monitoring and controlling the climate control system.
Provides real-time data display, historical charts, and manual override controls.
"""

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import logging
import time
from datetime import datetime
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Dashboard:
    """
    Web dashboard for the climate control system.
    """
    
    def __init__(self, config: dict = None, data_logger=None, control_engine=None, 
                 actuator_controller=None, sensor=None):
        """
        Initialize the dashboard.
        
        Args:
            config: Configuration dictionary
            data_logger: DataLogger instance
            control_engine: HybridControlEngine instance
            actuator_controller: ActuatorController instance
            sensor: SHT35Sensor instance
        """
        self.config = config or {}
        dashboard_config = self.config.get('dashboard', {})
        
        self.host = dashboard_config.get('host', '0.0.0.0')
        self.port = dashboard_config.get('port', 5000)
        self.refresh_interval = dashboard_config.get('refresh_interval', 2)
        self.chart_history_hours = dashboard_config.get('chart_history_hours', 24)
        
        # System components
        self.data_logger = data_logger
        self.control_engine = control_engine
        self.actuator_controller = actuator_controller
        self.sensor = sensor
        
        # Manual override state
        self.manual_override = False
        self.manual_states = {
            'pump': False,
            'chiller': False,
            'dehumidifier': False
        }
        
        # Flask app
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'climate_control_secret_key_2024'
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        # Setup routes
        self._setup_routes()
        self._setup_socketio()
        
        logger.info(f"Dashboard initialized on {self.host}:{self.port}")
    
    def _setup_routes(self):
        """Setup Flask routes."""
        
        @self.app.route('/')
        def index():
            """Main dashboard page."""
            return render_template('dashboard.html')
        
        @self.app.route('/api/current')
        def get_current_data():
            """Get current sensor readings and system state."""
            try:
                # Get sensor reading
                temp, humidity = None, None
                if self.sensor:
                    temp, humidity = self.sensor.read()
                
                # Get control engine state
                engine_stats = {}
                if self.control_engine:
                    engine_stats = self.control_engine.get_statistics()
                
                # Get actuator states
                actuator_status = {}
                if self.actuator_controller:
                    actuator_status = self.actuator_controller.get_status()
                
                data = {
                    'timestamp': time.time(),
                    'datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'sensor': {
                        'temperature': temp,
                        'humidity': humidity
                    },
                    'control': engine_stats,
                    'actuators': actuator_status,
                    'manual_override': self.manual_override
                }
                
                return jsonify(data)
                
            except Exception as e:
                logger.error(f"Error getting current data: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/history')
        def get_history():
            """Get historical data for charts."""
            try:
                hours = request.args.get('hours', self.chart_history_hours, type=int)
                
                if not self.data_logger:
                    return jsonify({'error': 'Data logger not available'}), 500
                
                readings = self.data_logger.get_recent_readings(hours=hours, limit=1000)
                
                # Format for charts
                timestamps = []
                temperatures = []
                humidities = []
                
                for reading in reversed(readings):
                    timestamps.append(reading['datetime'])
                    temperatures.append(reading['temperature'])
                    humidities.append(reading['humidity'])
                
                data = {
                    'timestamps': timestamps,
                    'temperatures': temperatures,
                    'humidities': humidities
                }
                
                return jsonify(data)
                
            except Exception as e:
                logger.error(f"Error getting history: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/events')
        def get_events():
            """Get recent system events."""
            try:
                hours = request.args.get('hours', 24, type=int)
                severity = request.args.get('severity', None)
                
                if not self.data_logger:
                    return jsonify({'error': 'Data logger not available'}), 500
                
                events = self.data_logger.get_system_events(hours=hours, severity=severity)
                
                return jsonify({'events': events})
                
            except Exception as e:
                logger.error(f"Error getting events: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/statistics')
        def get_statistics():
            """Get system statistics."""
            try:
                stats = {}
                
                if self.data_logger:
                    stats['database'] = self.data_logger.get_statistics()
                
                if self.control_engine:
                    stats['control'] = self.control_engine.get_statistics()
                
                if self.actuator_controller:
                    stats['actuators'] = self.actuator_controller.get_status()
                
                return jsonify(stats)
                
            except Exception as e:
                logger.error(f"Error getting statistics: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/export', methods=['POST'])
        def export_data():
            """Export data to CSV."""
            try:
                hours = request.json.get('hours', 24)
                
                if not self.data_logger:
                    return jsonify({'error': 'Data logger not available'}), 500
                
                filepath = self.data_logger.export_to_csv(hours=hours)
                
                return jsonify({
                    'success': True,
                    'filepath': filepath,
                    'message': f'Exported {hours} hours of data'
                })
                
            except Exception as e:
                logger.error(f"Error exporting data: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/preset', methods=['POST'])
        def set_preset():
            """Set produce type preset."""
            try:
                preset_name = request.json.get('preset')
                
                if not self.control_engine:
                    return jsonify({'error': 'Control engine not available'}), 500
                
                success = self.control_engine.load_preset(preset_name)
                
                if success:
                    return jsonify({
                        'success': True,
                        'message': f'Loaded preset: {preset_name}'
                    })
                else:
                    return jsonify({'error': 'Preset not found'}), 404
                
            except Exception as e:
                logger.error(f"Error setting preset: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/manual_override', methods=['POST'])
        def set_manual_override():
            """Enable/disable manual override and control actuators."""
            try:
                data = request.json
                
                if not self.actuator_controller:
                    return jsonify({'error': 'Actuator controller not available'}), 500
                
                # Check if safety allows manual override
                safety_config = self.config.get('safety', {})
                if not safety_config.get('enable_manual_override', True):
                    return jsonify({'error': 'Manual override is disabled'}), 403
                
                # Enable/disable override
                if 'enabled' in data:
                    self.manual_override = data['enabled']
                    logger.info(f"Manual override {'enabled' if self.manual_override else 'disabled'}")
                
                # Control actuators if override is enabled
                if self.manual_override:
                    if 'pump' in data:
                        self.manual_states['pump'] = data['pump']
                        self.actuator_controller.set_pump(data['pump'])
                    
                    if 'chiller' in data:
                        self.manual_states['chiller'] = data['chiller']
                        self.actuator_controller.set_chiller(data['chiller'])
                    
                    if 'dehumidifier' in data:
                        self.manual_states['dehumidifier'] = data['dehumidifier']
                        self.actuator_controller.set_dehumidifier(data['dehumidifier'])
                
                return jsonify({
                    'success': True,
                    'manual_override': self.manual_override,
                    'states': self.manual_states
                })
                
            except Exception as e:
                logger.error(f"Error in manual override: {e}")
                return jsonify({'error': str(e)}), 500
    
    def _setup_socketio(self):
        """Setup SocketIO event handlers for real-time updates."""
        
        @self.socketio.on('connect')
        def handle_connect():
            logger.info('Client connected to dashboard')
            emit('status', {'message': 'Connected to climate control system'})
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            logger.info('Client disconnected from dashboard')
        
        @self.socketio.on('request_update')
        def handle_update_request():
            """Handle request for real-time data update."""
            try:
                # Get current data
                temp, humidity = None, None
                if self.sensor:
                    temp, humidity = self.sensor.read()
                
                engine_state = {}
                if self.control_engine:
                    engine_state = {
                        'mode': self.control_engine.current_mode.value,
                        'targets': {
                            'temperature': self.control_engine.temp_target,
                            'humidity': self.control_engine.humidity_target
                        }
                    }
                
                actuator_state = {}
                if self.actuator_controller:
                    status = self.actuator_controller.get_status()
                    actuator_state = {
                        'pump': status['pump']['state'],
                        'chiller': status['chiller']['state'],
                        'dehumidifier': status['dehumidifier']['state'],
                        'water_level_ok': status['water_level_ok']
                    }
                
                data = {
                    'timestamp': time.time(),
                    'temperature': temp,
                    'humidity': humidity,
                    'control': engine_state,
                    'actuators': actuator_state,
                    'manual_override': self.manual_override
                }
                
                emit('update', data)
                
            except Exception as e:
                logger.error(f"Error sending update: {e}")
                emit('error', {'message': str(e)})
    
    def run(self, debug=False):
        """
        Run the dashboard server.
        
        Args:
            debug: Enable Flask debug mode
        """
        logger.info(f"Starting dashboard on http://{self.host}:{self.port}")
        self.socketio.run(self.app, host=self.host, port=self.port, debug=debug, allow_unsafe_werkzeug=True)
    
    def run_background(self):
        """Run the dashboard in a background thread."""
        thread = threading.Thread(target=self.run, kwargs={'debug': False})
        thread.daemon = True
        thread.start()
        logger.info("Dashboard running in background thread")
        return thread


# Example usage and testing
if __name__ == "__main__":
    print("Dashboard Test")
    print("-" * 40)
    print("Starting dashboard in standalone mode...")
    print("Navigate to http://localhost:5000 to view")
    
    # Create dashboard with no system components (for testing)
    dashboard = Dashboard()
    dashboard.run(debug=True)

