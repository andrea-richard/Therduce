# Product Requirements Document (PRD)
## Low-Cost Climate Control System for Produce Trucks

**Project Name:** Therduce Climate Control System  
**Version:** 1.0  
**Date:** November 2024  
**Challenge:** MIT Hackathon - Tata-Cornell Food Loss and Waste Challenge

---

## Executive Summary

This PRD outlines a low-cost, intelligent climate control system that retrofits into existing un-insulated produce trucks to prevent post-harvest food spoilage during transit. The system addresses food loss and waste (FLW) in Low- and Middle-Income Countries (LMICs) by maintaining optimal temperature and humidity conditions during transportation.

### Problem Statement

Post-harvest food loss in LMICs is a critical issue, with significant losses occurring during transportation due to inadequate temperature and humidity control. Existing solutions (refrigerated trucks) are too expensive for smallholder farmers and small-scale distributors.

### Solution Overview

A retrofit climate control system using:
- **Hardware:** Raspberry Pi Compute Module 5, SHT35-DIS-B sensors, evaporative cooling, vapor compression chiller, dehumidifier
- **Software:** Python-based hybrid AI control system with real-time monitoring
- **Cost Target:** < $500 per unit (vs. $20,000+ for refrigerated trucks)

---

## System Architecture

### Hardware Components

| Component | Model/Type | Function | Estimated Cost |
|-----------|-----------|----------|----------------|
| Controller | Raspberry Pi CM5 | Main processing unit | $45 |
| Temp/Humidity Sensor | SHT35-DIS-B | Climate monitoring | $10 |
| Water Pump | 12V DC Pump | Evaporative cooling | $25 |
| Spray Nozzles | Misting nozzles (4x) | Water distribution | $20 |
| Chiller | Vapor compression unit | Water cooling | $150 |
| Dehumidifier | Portable unit | Humidity control | $100 |
| Relays | 3-channel relay board | Actuator control | $15 |
| Water Reservoir | Food-safe tank (20L) | Water storage | $30 |
| Water Filter | Inline filter | Prevent nozzle clog | $15 |
| Wiring & Misc | Various | System integration | $40 |
| **Total** | | | **~$450** |

### Software Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Main Control Loop                        │
│                      (main.py)                               │
└────────────┬────────────────────────────────┬───────────────┘
             │                                │
    ┌────────▼────────┐              ┌───────▼────────┐
    │  Sensor Module  │              │  Data Logger   │
    │  (sensors.py)   │              │(data_logger.py)│
    │                 │              │                │
    │  SHT35-DIS-B    │              │  SQLite DB     │
    │  I2C Interface  │              │  CSV Export    │
    └────────┬────────┘              └───────┬────────┘
             │                                │
    ┌────────▼─────────────────────┐         │
    │   AI Control Engine          │         │
    │   (control_engine.py)        │         │
    │                              │         │
    │   • Rule-based Control       │         │
    │   • Predictive Logic         │◄────────┘
    │   • Multi-objective Opt      │
    └────────┬─────────────────────┘
             │
    ┌────────▼────────┐              ┌────────────────┐
    │Actuator Control │              │  Web Dashboard │
    │ (actuators.py)  │              │ (dashboard.py) │
    │                 │              │                │
    │  • Water Pump   │              │  Flask + Chart │
    │  • Chiller      │◄─────────────┤  Real-time     │
    │  • Dehumidifier │              │  Manual Ctrl   │
    └─────────────────┘              └────────────────┘
```

---

## Functional Requirements

### FR-1: Environmental Monitoring

**Priority:** Critical

The system SHALL continuously monitor temperature and humidity inside the truck cargo area.

**Acceptance Criteria:**
- Temperature readings accurate to ±0.5°C
- Humidity readings accurate to ±2% RH
- Reading frequency: every 2 seconds (configurable)
- Sensor failure detection with automatic fallback

**Implementation:**
- `sensors.py` - SHT35Sensor class
- I2C communication at address 0x44 or 0x45
- CRC validation for data integrity
- Reading history for validation (detect anomalies)

---

### FR-2: Hybrid AI Control System

**Priority:** Critical

The system SHALL use a hybrid AI approach combining rule-based control with predictive logic to maintain optimal conditions.

#### FR-2.1: Rule-Based Control

**Rules:**
1. **Temperature Control**
   - Target: 2-8°C (configurable per produce type)
   - Action: Activate cooling when temp > target + hysteresis
   - Emergency: Maximum cooling if temp > 15°C

2. **Humidity Control**
   - Target: 85-95% RH (configurable)
   - Action: Activate dehumidifier when humidity > target + hysteresis
   - Prevent: Don't use evaporative cooling if humidity already high

3. **Safety Rules**
   - Minimum 10 seconds between actuator state changes
   - Maximum runtime limits (pump: 10min, chiller: 30min, dehumidifier: 20min)
   - Don't run pump if water level low
   - Emergency shutdown at critical temperature

#### FR-2.2: Predictive Logic

**Features:**
1. **Rate of Change Detection**
   - Calculate temperature rate (°C/min) over 60-second window
   - Calculate humidity rate (%/min) over 60-second window
   - Warning thresholds: 0.5°C/min, 2%/min

2. **Anticipatory Control**
   - Predict temperature 5 minutes ahead using linear extrapolation
   - Activate cooling before threshold breach if trend continues
   - Adjust strategy based on rate severity

3. **Multi-Objective Optimization**
   - Priority weights: Temperature (10), Humidity (7), Energy (3)
   - Prefer evaporative cooling over chiller (energy efficient)
   - Coordinate cooling and dehumidification to avoid conflicts

**Acceptance Criteria:**
- System prevents 90%+ of threshold breaches via prediction
- Energy consumption 30-50% lower than continuous operation
- No oscillation (mode switches < 6/hour in stable conditions)

**Implementation:**
- `control_engine.py` - HybridControlEngine class
- CoolingMode enum: IDLE, EVAPORATIVE, CHILLER, DEHUMIDIFY, COOL_AND_DEHUMIDIFY, EMERGENCY
- ControlDecision class with reasoning and priority
- History-based trend analysis using deque (20 samples)

---

### FR-3: Actuator Control

**Priority:** Critical

The system SHALL safely control all actuators (pump, chiller, dehumidifier) via GPIO.

**Requirements:**
- GPIO control using BCM pin numbering
- Active-low relay logic (default safe state)
- Minimum cycle time enforcement (10 seconds)
- Maximum runtime protection
- Water level monitoring before pump activation

**Pin Assignments:**
- GPIO 17: Water pump relay
- GPIO 27: Chiller compressor relay
- GPIO 22: Dehumidifier relay
- GPIO 23: Water level sensor (input)

**Acceptance Criteria:**
- All actuators respond within 1 second of command
- Safety interlocks prevent unsafe operations
- Relay lifetime preserved (>100,000 cycles)

**Implementation:**
- `actuators.py` - ActuatorController class
- Actuator class with state tracking
- Safety check methods
- Emergency shutdown capability

---

### FR-4: Data Logging

**Priority:** High

The system SHALL log all sensor readings, control decisions, and system events to a persistent database.

**Requirements:**
- SQLite database with 4 tables:
  1. sensor_readings (temp, humidity, rates)
  2. control_decisions (mode, actuator states, reason)
  3. actuator_states (detailed tracking)
  4. system_events (startup, errors, warnings)

- CSV export functionality
- Automatic database cleanup when size exceeds limit
- Indexed queries for fast retrieval

**Acceptance Criteria:**
- No data loss during normal operation
- Export data for any time period in <5 seconds
- Database size self-managed (configurable max size)

**Implementation:**
- `data_logger.py` - DataLogger class
- Automatic schema creation
- Statistics and reporting methods

---

### FR-5: Web Dashboard

**Priority:** High

The system SHALL provide a web-based monitoring and control interface.

**Features:**

1. **Real-Time Display**
   - Current temperature and humidity
   - Operating mode
   - Actuator states (ON/OFF indicators)
   - Water level status
   - Last update timestamp

2. **Historical Charts**
   - Temperature over time (24 hours default)
   - Humidity over time
   - Interactive Plotly charts
   - Auto-refresh every 60 seconds

3. **Controls**
   - Produce type presets (leafy greens, berries, tomatoes, citrus)
   - Data export button
   - Manual override toggle
   - Individual actuator control (when override enabled)

4. **System Status**
   - Connection status
   - System events and alerts
   - Statistics and uptime

**Technical Requirements:**
- Flask web framework
- SocketIO for real-time updates
- Responsive design (mobile-friendly)
- Port 5000, accessible on local network

**Acceptance Criteria:**
- Dashboard loads in <3 seconds
- Real-time updates every 2 seconds
- Works on desktop and mobile browsers
- Manual override provides immediate control

**Implementation:**
- `dashboard.py` - Dashboard class with Flask routes
- `templates/dashboard.html` - Modern, responsive UI
- REST API endpoints + WebSocket events

---

## Non-Functional Requirements

### NFR-1: Performance

- **Control Loop:** Execute full cycle in <1 second (target: 200ms)
- **Sensor Reading:** <100ms per reading
- **Database Write:** <50ms per log entry
- **Dashboard Response:** <500ms for API calls

### NFR-2: Reliability

- **Uptime:** >99% during trip duration
- **Sensor Failure Handling:** Safe mode within 30 seconds
- **Graceful Shutdown:** Complete cleanup on SIGTERM/SIGINT
- **Error Recovery:** Automatic retry on transient errors

### NFR-3: Energy Efficiency

- **Idle Power:** <10W (RPi + sensors only)
- **Evaporative Mode:** ~50W (pump + occasional chiller)
- **Full Cooling:** <1000W total
- **Optimization:** Prefer low-power modes when possible

### NFR-4: Maintainability

- **Code Quality:** Python 3.9+, type hints, docstrings
- **Modularity:** Clear separation of concerns
- **Configuration:** YAML config file, no hardcoded values
- **Logging:** Comprehensive logs at appropriate levels
- **Documentation:** README, code comments, inline help

### NFR-5: Scalability

- **Database:** Handle 30+ days of continuous data
- **Multiple Sensors:** Architecture supports adding sensors
- **Network:** Dashboard supports multiple concurrent clients
- **Deployment:** Easy installation on any Raspberry Pi

---

## Configuration System

### config.yaml Structure

```yaml
sensor:
  i2c_address: 0x44
  i2c_bus: 1
  read_interval: 2.0

targets:
  temp_min: 2.0
  temp_target: 5.0
  temp_max: 8.0
  humidity_min: 85.0
  humidity_target: 90.0
  humidity_max: 95.0
  temp_rate_warning: 0.5
  humidity_rate_warning: 2.0

gpio:
  water_pump: 17
  chiller: 27
  dehumidifier: 22
  water_level_sensor: 23

actuators:
  min_cycle_time: 10
  max_pump_runtime: 600
  max_chiller_runtime: 1800
  max_dehumidifier_runtime: 1200
  spray_duration: 5
  spray_cooldown: 30

control:
  temp_hysteresis: 0.5
  humidity_hysteresis: 2.0
  prediction_window: 5
  history_samples: 20
  priority_temperature: 10
  priority_humidity: 7
  priority_energy: 3

logging:
  database_path: "climate_data.db"
  log_interval: 5
  csv_export_dir: "exports"
  max_db_size_mb: 100

dashboard:
  enabled: true
  host: "0.0.0.0"
  port: 5000
  refresh_interval: 2
  chart_history_hours: 24

safety:
  enable_water_level_check: true
  emergency_shutdown_temp: 15.0
  sensor_timeout: 30
  enable_manual_override: true

presets:
  leafy_greens: {temp_target: 4.0, humidity_target: 95.0}
  berries: {temp_target: 2.0, humidity_target: 90.0}
  tomatoes: {temp_target: 13.0, humidity_target: 85.0}
  citrus: {temp_target: 8.0, humidity_target: 85.0}
```

---

## API Specification

### REST Endpoints

#### GET /api/current
Returns current sensor readings and system state.

**Response:**
```json
{
  "timestamp": 1699564800.0,
  "datetime": "2024-11-09 14:30:00",
  "sensor": {
    "temperature": 5.2,
    "humidity": 89.5
  },
  "control": {
    "current_mode": "evaporative",
    "decisions_made": 1234,
    "targets": {
      "temperature": 5.0,
      "humidity": 90.0
    }
  },
  "actuators": {
    "pump": {"state": "ON", "runtime": 45.2},
    "chiller": {"state": "OFF"},
    "dehumidifier": {"state": "OFF"},
    "water_level_ok": true
  },
  "manual_override": false
}
```

#### GET /api/history?hours=24
Returns historical sensor readings.

**Response:**
```json
{
  "timestamps": ["2024-11-09 14:00:00", ...],
  "temperatures": [5.2, 5.3, ...],
  "humidities": [89.5, 90.1, ...]
}
```

#### POST /api/preset
Load produce type preset.

**Request:**
```json
{
  "preset": "leafy_greens"
}
```

#### POST /api/manual_override
Enable/disable manual override and control actuators.

**Request:**
```json
{
  "enabled": true,
  "pump": true,
  "chiller": false,
  "dehumidifier": false
}
```

#### POST /api/export
Export data to CSV.

**Request:**
```json
{
  "hours": 24
}
```

### WebSocket Events

#### Client -> Server

- `connect`: Establish connection
- `disconnect`: Close connection  
- `request_update`: Request current data

#### Server -> Client

- `status`: Connection status message
- `update`: Real-time data update
- `error`: Error message

---

## Control Logic Flowchart

```
START
  │
  ├─► Read Temperature & Humidity
  │         │
  │         ├─► Calculate Rate of Change
  │         │
  │         ├─► Predict Future Values (5 min ahead)
  │         │
  │         └─► Assess Situation
  │                   │
  │                   ├─► Temperature Critical? (>15°C)
  │                   │     YES ─► EMERGENCY MODE (All cooling ON)
  │                   │     NO ─▼
  │                   │
  │                   ├─► Temperature Very High? (>8°C)
  │                   │     YES ─► Humidity High? ─► CHILLER + DEHUMIDIFIER
  │                   │                            ─► CHILLER + PUMP
  │                   │     NO ─▼
  │                   │
  │                   ├─► Humidity Very High? (>95%)
  │                   │     YES ─► Temp High? ─► CHILLER + DEHUMIDIFIER
  │                   │                        ─► DEHUMIDIFIER ONLY
  │                   │     NO ─▼
  │                   │
  │                   ├─► Temperature Moderately High? (>6°C)
  │                   │     YES ─► Humidity OK? ─► EVAPORATIVE COOLING
  │                   │                         ─► CHILLER
  │                   │     NO ─▼
  │                   │
  │                   ├─► Predictive Warning?
  │                   │     YES ─► ANTICIPATORY EVAPORATIVE
  │                   │     NO ─▼
  │                   │
  │                   └─► IDLE (Conditions Optimal)
  │
  ├─► Execute Decision
  │     │
  │     ├─► Manual Override Active?
  │     │     YES ─► Skip (but log decision)
  │     │     NO ─▼
  │     │
  │     └─► Set Actuator States via GPIO
  │
  ├─► Safety Checks
  │     │
  │     ├─► Check Runtime Limits
  │     ├─► Check Water Level
  │     └─► Force Off if Needed
  │
  ├─► Log Data
  │     │
  │     ├─► Sensor Readings → Database
  │     ├─► Control Decision → Database
  │     └─► Actuator States → Database
  │
  ├─► Sleep (to maintain interval)
  │
  └─► LOOP
```

---

## Testing Strategy

### Unit Tests

1. **Sensor Module**
   - I2C communication mock
   - CRC validation
   - Reading validation
   - Simulation mode

2. **Actuator Module**
   - GPIO mock
   - State transitions
   - Safety interlocks
   - Timing constraints

3. **Control Engine**
   - Decision logic for various scenarios
   - Rate calculation
   - Prediction accuracy
   - Mode selection

4. **Data Logger**
   - Database operations
   - CSV export
   - Query performance
   - Cleanup operations

### Integration Tests

1. **Sensor → Control Engine**
   - Reading flow
   - History management
   - Decision triggering

2. **Control Engine → Actuators**
   - Command execution
   - Safety override
   - Manual control

3. **System → Dashboard**
   - API responses
   - WebSocket updates
   - Control feedback

### Field Tests

1. **Empty Truck Test** (No produce)
   - System stability
   - Temperature range achievement
   - Energy consumption baseline

2. **Loaded Truck Test** (With produce)
   - Cooling effectiveness
   - Humidity management
   - Produce quality after transit

3. **Long Duration Test** (8+ hours)
   - System reliability
   - Database performance
   - No memory leaks

4. **Edge Case Tests**
   - Sensor failure recovery
   - Power interruption
   - Network loss (dashboard)
   - Water reservoir empty

---

## Deployment Instructions

### 1. Hardware Setup

1. Mount Raspberry Pi CM5 in waterproof enclosure
2. Install SHT35-DIS-B sensor in cargo area (avoid direct contact with produce)
3. Mount water reservoir securely
4. Install pump and spray nozzles (4 corners for even distribution)
5. Position chiller unit
6. Mount dehumidifier unit
7. Wire relays to actuators
8. Connect GPIO pins per configuration
9. Install water level sensor in reservoir
10. Power all components (12V DC from truck battery + voltage regulators)

### 2. Software Installation

```bash
# 1. Update Raspberry Pi OS
sudo apt-get update && sudo apt-get upgrade -y

# 2. Enable I2C
sudo raspi-config
# Interface Options → I2C → Enable

# 3. Install system dependencies
sudo apt-get install python3 python3-pip python3-venv -y
sudo apt-get install python3-dev libatlas-base-dev -y

# 4. Clone project
cd /home/pi
git clone <repository-url>
cd climate_control

# 5. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 6. Install Python packages
pip install -r requirements.txt

# 7. Test hardware
python3 -c "from sensors import SHT35Sensor; s = SHT35Sensor(); print(s.read())"

# 8. Configure system
nano config.yaml
# Adjust settings for your hardware and produce type

# 9. Test run
sudo python3 main.py
# Ctrl+C to stop

# 10. Install as service (optional, for auto-start)
sudo cp climate-control.service /etc/systemd/system/
sudo systemctl enable climate-control.service
sudo systemctl start climate-control.service
```

### 3. Calibration

1. Place reference thermometer in cargo area
2. Run system for 30 minutes
3. Compare sensor readings with reference
4. Adjust calibration offsets in code if needed:
   ```python
   sensor.set_calibration(temp_offset=0.5, humidity_offset=-1.0)
   ```

### 4. Validation

1. Load produce (test load)
2. Monitor dashboard for 2 hours
3. Verify:
   - Temperature stays within target ±1°C
   - Humidity stays within target ±5%
   - No sensor errors
   - Actuators cycle appropriately
4. Check produce quality after test period

---

## Success Metrics

### Technical Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Temperature Stability | ±1°C from target | Dashboard/logs |
| Humidity Stability | ±5% from target | Dashboard/logs |
| System Uptime | >99% | Log analysis |
| Sensor Accuracy | ±0.5°C, ±2% RH | Reference comparison |
| Control Latency | <1 second | Code profiling |
| Energy Efficiency | 50% of continuous cooling | Power meter |

### Impact Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Food Loss Reduction | >40% vs. uncontrolled | Weight/quality assessment |
| Cost per Trip | <$5 (power + water) | Consumption tracking |
| Payback Period | <20 trips | Cost analysis |
| Produce Shelf Life | +3-5 days | Quality tests |
| User Satisfaction | >8/10 | Surveys |

---

## Risk Assessment

### Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Sensor Failure | Medium | High | Redundant sensors, fallback mode |
| Power Loss | Medium | High | Battery backup, auto-restart |
| Water Depletion | High | Medium | Level monitoring, alerts |
| Relay Failure | Low | High | Quality relays, cycle limits |
| Software Bug | Medium | Medium | Extensive testing, watchdog |

### Operational Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| User Misunderstanding | Medium | Medium | Clear UI, training materials |
| Maintenance Neglect | High | Medium | Automated alerts, simple design |
| Damage in Transit | Medium | High | Robust enclosures, secure mounting |
| Theft | Low | High | Lockable boxes, insurance |

---

## Future Enhancements

### Phase 2 Features

1. **Machine Learning Integration**
   - Train models on historical data
   - Predict optimal cooling schedules
   - Adaptive learning per produce type

2. **Multi-Sensor Array**
   - Multiple temp/humidity sensors
   - Gradient mapping
   - Localized control

3. **GPS Integration**
   - Route optimization
   - Environmental prediction based on location
   - Driver alerts

4. **Cloud Connectivity**
   - Remote monitoring
   - Fleet management
   - Data aggregation for insights

5. **Advanced Actuators**
   - Variable-speed pump (PWM control)
   - Zoned cooling
   - Air circulation fans

### Phase 3 (Commercialization)

1. Custom PCB design
2. Injection-molded enclosures
3. Mobile app (iOS/Android)
4. Professional installation service
5. Subscription-based monitoring

---

## Bill of Materials (Detailed)

### Electronics

| Item | Part Number | Qty | Unit Cost | Total |
|------|------------|-----|-----------|-------|
| Raspberry Pi CM5 | CM5 | 1 | $45 | $45 |
| SHT35-DIS-B Sensor | SHT35-DIS-B | 1 | $10 | $10 |
| 3-Ch Relay Module | 5V 10A | 1 | $15 | $15 |
| Power Supply 12V 5A | PSU-12V-5A | 1 | $20 | $20 |
| Step-down 12V→5V | LM2596 | 1 | $5 | $5 |
| Wire 18AWG | - | 10m | $0.50/m | $5 |
| Connectors | Various | - | - | $10 |

### Mechanical

| Item | Part Number | Qty | Unit Cost | Total |
|------|------------|-----|-----------|-------|
| Water Pump 12V | PUMP-12V | 1 | $25 | $25 |
| Misting Nozzles | NOZZLE-0.2mm | 4 | $5 | $20 |
| Chiller Unit | CHILLER-12V | 1 | $150 | $150 |
| Dehumidifier | DEHUM-12V | 1 | $100 | $100 |
| Water Reservoir | TANK-20L | 1 | $30 | $30 |
| Water Filter | FILTER-10 | 1 | $15 | $15 |
| Tubing 6mm | - | 5m | $2/m | $10 |
| Mounting Hardware | - | - | - | $20 |

### Enclosures

| Item | Part Number | Qty | Unit Cost | Total |
|------|------------|-----|-----------|-------|
| Waterproof Box (Pi) | IP65-150x110x70 | 1 | $15 | $15 |
| Cable Glands | PG9 | 4 | $2 | $8 |

**Total BOM Cost: ~$468**  
**Target Selling Price: $799**  
**Gross Margin: 41%**

---

## Compliance & Standards

### Safety

- **Electrical:** Follow local electrical codes
- **Food Safety:** Use food-grade materials for water system
- **EMC:** Shield electronics to prevent interference

### Environmental

- **RoHS:** Use RoHS-compliant components
- **Water Usage:** Efficient design, ~2L/hour max
- **Refrigerant:** Use environmentally friendly refrigerants

### Data Privacy

- **Local Storage:** All data stored locally by default
- **Cloud Optional:** User choice for cloud features
- **No PII:** System doesn't collect personal information

---

## Support & Maintenance

### Routine Maintenance (Weekly)

1. Check water reservoir level
2. Inspect spray nozzles for clogs
3. Verify sensor readings (spot check)
4. Review system logs for errors

### Preventive Maintenance (Monthly)

1. Clean/replace water filter
2. Check relay operation
3. Inspect wiring connections
4. Update software if available
5. Export and backup data

### Troubleshooting Guide

See README.md for detailed troubleshooting steps.

---

## Conclusion

This climate control system provides a practical, affordable solution to post-harvest food loss in LMICs. By combining intelligent control algorithms with low-cost hardware, the system maintains optimal conditions for perishable produce during transit, potentially reducing food losses by 40%+ at a fraction of the cost of refrigerated trucks.

The hybrid AI approach ensures reliable operation while minimizing energy consumption, making it economically viable for smallholder farmers and small-scale distributors who are often excluded from existing cold chain solutions.

**Key Innovations:**
1. **Hybrid AI Control:** Combines rule-based safety with predictive optimization
2. **Multi-Mode Cooling:** Energy-efficient evaporative + high-power chiller as needed
3. **Retrofittable Design:** Works with existing un-insulated trucks
4. **Real-Time Monitoring:** Web dashboard accessible from any device
5. **Low Cost:** <$500 hardware cost vs. $20,000+ for alternatives

This solution directly addresses the Tata-Cornell Food Loss and Waste challenge by providing scalable, context-relevant technology to reduce food loss in developing countries.

---

**Document Version:** 1.0  
**Last Updated:** November 2024  
**Authors:** Therduce Team  
**Status:** Implementation Complete

