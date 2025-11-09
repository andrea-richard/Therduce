from flask import Flask, request, jsonify, send_from_directory
from sensors import SHT35Sensor
from dashboard import Dashboard
from control_engine import HybridControlEngine, CoolingMode
from actuators import ActuatorController
import json
import os

# Initialize components
sensor = SHT35Sensor()
actuator_controller = ActuatorController()
control_engine = HybridControlEngine()

# Initialize dashboard with all components
dashboard = Dashboard(
    config={
        'dashboard': {
            'host': '0.0.0.0',
            'port': 5000
        }
    },
    sensor=sensor,
    control_engine=control_engine,
    actuator_controller=actuator_controller
)

app = Flask(__name__, 
    static_folder='../app',  # location of static files
    template_folder='../app'  # location of template files
)

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'app.html')
    
@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files from the app directory"""
    return send_from_directory(app.static_folder, filename)

@app.route('/update_settings', methods=['POST'])
def update_settings():
    try:
        data = request.get_json()
        temperature = float(data.get('temperature', 22))
        humidity = float(data.get('humidity', 50))
        produce = data.get('produce', 'mango')
        
        # Update control engine targets via API
        control_engine.set_targets(temp_target=temperature, humidity_target=humidity)
        
        # Update sensor calibration to match desired values
        current_temp, current_humidity = sensor.read()
        if current_temp is not None and current_humidity is not None:
            temp_offset = temperature - current_temp
            humidity_offset = humidity - current_humidity
            sensor.set_calibration(temp_offset, humidity_offset)
            
            # Make a control decision based on new settings and execute it
            decision = control_engine.make_decision(current_temp, current_humidity)
            control_engine.execute_decision(decision)

            # Notify dashboard clients immediately (if socketio is available)
            try:
                import time
                # Build control state matching Dashboard._setup_socketio.handle_update_request
                engine_state = {
                    'mode': control_engine.current_mode.value,
                    'targets': {
                        'temperature': control_engine.temp_target,
                        'humidity': control_engine.humidity_target
                    }
                }

                # Build actuator state similar to Dashboard expectations
                actuator_state = {}
                try:
                    status = actuator_controller.get_status() if actuator_controller else {}
                    if status:
                        actuator_state = {
                            'pump': status['pump']['state'],
                            'chiller': status['chiller']['state'],
                            'dehumidifier': status['dehumidifier']['state'],
                            'water_level_ok': status.get('water_level_ok', True)
                        }
                except Exception:
                    actuator_state = {}

                payload = {
                    'timestamp': time.time(),
                    'temperature': current_temp,
                    'humidity': current_humidity,
                    'control': engine_state,
                    'actuators': actuator_state,
                    'manual_override': getattr(dashboard, 'manual_override', False)
                }

                if hasattr(dashboard, 'socketio') and dashboard.socketio:
                    dashboard.socketio.emit('update', payload, broadcast=True)
            except Exception:
                # ignore notify errors
                pass
        
        return jsonify({
            'status': 'success',
            'message': f'Settings updated - Target: {temperature}°C, {humidity}% RH for {produce}'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/current_readings', methods=['GET'])
def get_readings():
    try:
        temp, humidity = sensor.read()
        return jsonify({
            'temperature': temp,
            'humidity': humidity,
            'targets': {
                'temperature': control_engine.temp_target,
                'humidity': control_engine.humidity_target
            },
            'status': 'success'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

def run_dashboard():
    """Run the dashboard in the background"""
    dashboard.run_background()

if __name__ == '__main__':
    print("Dashboard starting...")
    # Start dashboard in background
    run_dashboard()
    
    # Enable CORS for development
    from flask_cors import CORS
    CORS(app)
    
    # Run the web interface
    app.run(host='0.0.0.0', port=5001)  # Note: Using port 5001 since dashboard uses 5000