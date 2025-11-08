# Setting Up on Mac (Development Environment)

## ✅ Complete Mac Setup Guide

This guide covers everything you need to develop and demo the climate control system on your Mac, **without any hardware**.

---

## 🚀 Quick Start (5 Minutes)

### Step 1: Navigate to Project

```bash
cd /Users/janiceshen/Desktop/Malcolm/Therduce/climate_control
```

### Step 2: Create Virtual Environment (First Time Only)

```bash
python3 -m venv venv
```

### Step 3: Activate Virtual Environment

```bash
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt.

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 5: Test Sensor (Optional)

```bash
python3 sensors.py
```

**Expected output:**
```
⚠️  Running in SIMULATION MODE
   (This is normal when sensor is not connected or on non-Pi systems)
   All features work - just with simulated data

Reading 1 [SIM]: 4.72°C, 90.4% RH
...
✅ Test complete!
```

### Step 6: Run the System

```bash
python3 main.py
```

**⚠️ IMPORTANT: Do NOT use `sudo` on Mac!**

- ❌ `sudo python3 main.py` - This will fail (can't find packages)
- ✅ `python3 main.py` - This works perfectly

### Step 7: Open Dashboard

Open your browser and go to:
```
http://localhost:5000
```

---

## 🎯 Easy Way: Use the Run Script

I've created a helper script that does everything automatically:

```bash
cd climate_control
./run.sh
```

This script:
- ✅ Activates virtual environment automatically
- ✅ Detects Mac vs Pi
- ✅ Runs with correct permissions
- ✅ Installs dependencies if needed

---

## 🔧 Detailed Setup Instructions

### Prerequisites

- **Python 3.9+** (check with `python3 --version`)
- **macOS** (any recent version)

### Complete First-Time Setup

```bash
# 1. Navigate to project directory
cd /Users/janiceshen/Desktop/Malcolm/Therduce/climate_control

# 2. Create virtual environment
python3 -m venv venv

# 3. Activate virtual environment
source venv/bin/activate

# 4. Upgrade pip (recommended)
pip install --upgrade pip

# 5. Install all dependencies
pip install -r requirements.txt

# 6. Test sensor (should work in simulation mode)
python3 sensors.py

# 7. Run the full system
python3 main.py
```

### Every Time You Run

```bash
cd climate_control
source venv/bin/activate  # Look for (venv) in prompt!
python3 main.py           # NO sudo!
```

---

## 🎭 Simulation Mode Explained

### What is Simulation Mode?

The system **automatically detects** when hardware isn't available and switches to simulation mode. This means:

- ✅ **No errors** - graceful fallback
- ✅ **All features work** - AI, dashboard, logging
- ✅ **Realistic data** - simulated temp/humidity readings
- ✅ **Perfect for development** - test everything without hardware

### How It Works

1. **Sensor Code** checks if I2C is available
2. **If not found** (Mac, no sensor, etc.), it uses simulation
3. **GPIO operations** are logged instead of controlling real hardware
4. **Everything else works normally**

### What Gets Simulated

- **Temperature:** ~5°C with realistic variations (±0.5°C)
- **Humidity:** ~90% RH with realistic variations (±2%)
- **GPIO:** Commands logged instead of controlling relays

### What Works Normally

- ✅ AI control engine (makes real decisions)
- ✅ Dashboard (web interface)
- ✅ Data logging (SQLite database)
- ✅ CSV export
- ✅ All features and logic

---

## ⚠️ Common Issues & Fixes

### Issue 1: `ModuleNotFoundError: No module named 'yaml'`

**Cause:** You used `sudo` or virtual environment not activated

**Fix:**
```bash
# Make sure venv is activated (look for (venv) in prompt)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run WITHOUT sudo
python3 main.py
```

### Issue 2: `Permission denied` or `Address already in use`

**Fix:**
```bash
# Check if something is using port 5000
lsof -ti:5000 | xargs kill

# Or change port in config.yaml
```

### Issue 3: Virtual environment not activated

**Check:** Look for `(venv)` in your terminal prompt

**Fix:**
```bash
source venv/bin/activate
```

### Issue 4: Sensor test shows errors

**Old behavior (before fix):** Would show error about `/dev/i2c-1`

**New behavior (after fix):** Automatically uses simulation mode, no errors!

If you still see errors, make sure you have the latest code.

---

## 🍎 Mac vs 🍓 Raspberry Pi

### On Mac (What You're Doing Now):

```bash
# No sudo needed!
cd climate_control
source venv/bin/activate
python3 main.py
```

**Characteristics:**
- GPIO is mocked (simulated)
- I2C not available (uses simulation)
- No special permissions needed
- Perfect for development

### On Raspberry Pi (Production):

```bash
# Sudo IS needed for GPIO
cd climate_control
source venv/bin/activate
sudo python3 main.py
```

**Characteristics:**
- Real GPIO hardware
- Real I2C sensors
- Requires root for GPIO access
- Production deployment

**Key Difference:** On Mac, **never use `sudo`**. On Pi, **always activate venv first, then use `sudo`**.

---

## 🧪 Testing Your Setup

### Test 1: Sensor Module

```bash
python3 sensors.py
```

**Expected:** Shows simulation mode with readings

### Test 2: Actuator Module

```bash
python3 actuators.py
```

**Expected:** Shows GPIO simulation

### Test 3: Control Engine

```bash
python3 control_engine.py
```

**Expected:** Shows AI decision-making examples

### Test 4: Full System

```bash
python3 main.py
```

**Expected:** 
- System starts without errors
- Dashboard available at http://localhost:5000
- Shows simulated sensor data
- AI makes control decisions

---

## 📊 What You'll See

### When System Starts:

```
╔════════════════════════════════════════════════════════╗
║     Climate Control System for Produce Trucks         ║
║     Post-Harvest Food Loss Prevention                 ║
║                                                        ║
║     Tata-Cornell Food Challenge - MIT Hackathon       ║
╚════════════════════════════════════════════════════════╝

WARNING:sensors:SMBus not available - running in simulation mode
INFO:sensors:I2C device /dev/i2c-1 not available - running in simulation mode
INFO:sensors:This is normal when running on non-Pi systems or when sensor is not connected
INFO:actuators:RPi.GPIO not available - running in simulation mode
INFO:__main__:System initialization complete
INFO:__main__:Starting main control loop
INFO:__main__:Dashboard available at http://0.0.0.0:5000
```

### In Dashboard:

- **Current Conditions:** Shows simulated temp/humidity
- **Control System:** Shows AI mode and decisions
- **Actuator Status:** Shows simulated states
- **Charts:** Historical data (if running for a while)

---

## 🎯 For Hackathon Demo

### Option 1: Demo on Mac (Recommended)

**Perfect for:**
- Showing the system works
- Demonstrating AI logic
- Displaying dashboard
- Explaining features

**Setup:**
```bash
cd climate_control
source venv/bin/activate
python3 main.py
```

**Tell Judges:**
- "Running in simulation mode for demo"
- "In production, connects to real sensors via I2C"
- "All AI logic and features are fully functional"
- "System automatically detects hardware availability"

### Option 2: Demo on Raspberry Pi

**If you have hardware:**
1. Set up Pi before hackathon
2. Enable I2C: `sudo raspi-config`
3. Connect sensor
4. Install system on Pi
5. Run at hackathon: `sudo python3 main.py`

---

## 🔍 Verification Checklist

Before you start developing, verify:

- [ ] Python 3.9+ installed (`python3 --version`)
- [ ] Virtual environment created (`ls venv/`)
- [ ] Virtual environment activated (see `(venv)` in prompt)
- [ ] Dependencies installed (`pip list` shows packages)
- [ ] Sensor test works (`python3 sensors.py` shows simulation mode)
- [ ] System runs (`python3 main.py` starts without errors)
- [ ] Dashboard accessible (`http://localhost:5000` works)

---

## 📝 Daily Workflow

### Starting Work:

```bash
# 1. Navigate to project
cd /Users/janiceshen/Desktop/Malcolm/Therduce/climate_control

# 2. Activate virtual environment
source venv/bin/activate

# 3. Run system
python3 main.py
```

### Stopping Work:

- Press `Ctrl+C` in terminal
- System shuts down gracefully

### Making Changes:

1. Edit code files
2. Stop system (`Ctrl+C`)
3. Restart system (`python3 main.py`)
4. Changes take effect immediately

---

## 🎓 Understanding the System

### File Structure:

```
climate_control/
├── main.py              # Main control loop
├── sensors.py           # Sensor interface (auto-simulation)
├── actuators.py         # GPIO control (auto-simulation)
├── control_engine.py    # AI decision engine
├── data_logger.py       # Database logging
├── dashboard.py         # Web interface
├── config.yaml          # Configuration
├── requirements.txt     # Dependencies
├── run.sh              # Helper script
└── templates/
    └── dashboard.html  # Web UI
```

### Key Points:

1. **Simulation is automatic** - no configuration needed
2. **All code works** - just with simulated data
3. **No hardware required** - perfect for development
4. **Production ready** - automatically uses real hardware when available

---

## 🐛 Troubleshooting

### "Command not found: python3"

**Fix:** Install Python 3.9+ from python.org or use Homebrew:
```bash
brew install python3
```

### "No module named 'smbus2'"

**This is normal on Mac!** The system uses simulation mode when smbus2 isn't available. No action needed.

### "Port 5000 already in use"

**Fix:**
```bash
# Find and kill process using port 5000
lsof -ti:5000 | xargs kill

# Or change port in config.yaml
```

### "Virtual environment not found"

**Fix:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Dashboard not loading

**Check:**
1. System is running (`python3 main.py` is active)
2. No errors in terminal
3. Try: `http://127.0.0.1:5000` instead of `localhost:5000`

---

## 📚 Additional Resources

- **I2C_SETUP_GUIDE.md** - I2C setup (for when you get a Pi)
- **RUNNING_THE_SYSTEM.md** - Detailed run instructions
- **QUICKSTART.md** - Fast hackathon demo guide
- **README.md** - Complete documentation

---

## ✅ Summary

### What You Need:

1. ✅ Mac with Python 3.9+
2. ✅ Virtual environment (one-time setup)
3. ✅ Dependencies installed (one-time setup)
4. ✅ That's it!

### What You DON'T Need:

- ❌ Raspberry Pi (for development)
- ❌ Sensors (simulated)
- ❌ Hardware (simulated)
- ❌ `sudo` (not needed on Mac)
- ❌ `raspi-config` (Pi-only tool)

### What Works:

- ✅ All Python code
- ✅ AI control engine
- ✅ Web dashboard
- ✅ Data logging
- ✅ All features

**Bottom Line:** You can develop, test, and demo the entire system on your Mac without any hardware. Simulation mode is automatic and works perfectly! 🎯

---

## 🚀 Ready to Go!

You're all set! Just run:

```bash
cd climate_control
source venv/bin/activate
python3 main.py
```

Then open: `http://localhost:5000`

Happy coding! 🎉
