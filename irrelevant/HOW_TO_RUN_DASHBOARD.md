# How to Run the Dashboard

## 🚀 Quick Start (3 Steps)

### Step 1: Open Terminal

Open Terminal on your Mac and navigate to the project:

```bash
cd /Users/janiceshen/Desktop/Malcolm/Therduce/climate_control
```

### Step 2: Activate Virtual Environment

```bash
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt.

### Step 3: Run the System

```bash
python3 main.py
```

**⚠️ Important:** Do NOT use `sudo` on Mac!

---

## 📊 Access the Dashboard

Once the system starts, you'll see output like:

```
╔════════════════════════════════════════════════════════╗
║     Climate Control System for Produce Trucks         ║
...
INFO:__main__:Dashboard available at http://0.0.0.0:5000
```

### Open in Browser:

**Option 1:** Click this link or copy-paste into browser:
```
http://localhost:5000
```

**Option 2:** Use the IP address:
```
http://127.0.0.1:5000
```

---

## 🎯 What You'll See

The dashboard shows:

1. **📊 Current Conditions**
   - Real-time temperature (°C)
   - Real-time humidity (%)
   - Connection status

2. **🎯 Control System**
   - Current operating mode (IDLE, EVAPORATIVE, CHILLER, etc.)
   - Target temperature and humidity
   - AI decision reasoning

3. **⚙️ Actuator Status**
   - Water pump (ON/OFF)
   - Chiller (ON/OFF)
   - Dehumidifier (ON/OFF)
   - Water level status

4. **🎮 Controls**
   - Produce type presets (Leafy Greens, Berries, Tomatoes, Citrus)
   - Data export button
   - Manual override toggle

5. **📈 Historical Charts**
   - 24-hour temperature trend
   - 24-hour humidity trend
   - Interactive (zoom, hover)

---

## 🛑 Stopping the Dashboard

To stop the system:

1. Go back to the terminal where it's running
2. Press `Ctrl+C`
3. Wait for graceful shutdown

---

## 🔧 Troubleshooting

### Dashboard Won't Load

**Check 1:** Is the system running?
- Look at terminal - should show "Dashboard available at..."
- If not, check for errors

**Check 2:** Try different URLs:
- `http://localhost:5000`
- `http://127.0.0.1:5000`
- `http://0.0.0.0:5000`

**Check 3:** Port already in use?
```bash
# Check if something is using port 5000
lsof -ti:5000

# Kill it if needed
lsof -ti:5000 | xargs kill
```

### "Connection Refused"

**Cause:** System not started or crashed

**Fix:**
1. Check terminal for errors
2. Make sure virtual environment is activated
3. Try running again: `python3 main.py`

### Dashboard Shows "Disconnected"

**Cause:** WebSocket connection issue

**Fix:**
- Refresh the page (F5 or Cmd+R)
- Check browser console for errors
- Make sure system is still running

---

## 📱 Access from Other Devices

If you want to access the dashboard from your phone or another computer on the same network:

1. **Find your Mac's IP address:**
   ```bash
   ifconfig | grep "inet " | grep -v 127.0.0.1
   ```
   Look for something like `192.168.1.XXX`

2. **Access from other device:**
   ```
   http://192.168.1.XXX:5000
   ```
   (Replace XXX with your actual IP)

**Note:** Make sure your Mac's firewall allows connections on port 5000.

---

## 🎨 Dashboard Features

### Real-Time Updates
- Updates every 2 seconds automatically
- Shows current sensor readings
- Displays current actuator states

### Interactive Charts
- Hover over data points for details
- Zoom in/out on time ranges
- Shows 24 hours of history

### Controls
- **Load Preset:** Select produce type and click "Load Preset"
- **Export Data:** Download CSV file with all logged data
- **Manual Override:** Toggle to manually control actuators

### Visual Indicators
- 🟢 Green dot = ON/Connected
- ⚪ Gray dot = OFF
- 🟡 Yellow dot = Warning
- 🔴 Red dot = Error/Low

---

## 💡 Pro Tips

1. **Keep Terminal Open:** The system runs in the terminal - keep it open while using dashboard

2. **Check Logs:** Terminal shows all system activity and decisions

3. **Refresh Charts:** Charts auto-update every 60 seconds, or refresh page manually

4. **Multiple Tabs:** You can open dashboard in multiple browser tabs

5. **Mobile Friendly:** Dashboard works on phones/tablets too!

---

## 🎯 Complete Example Session

```bash
# Terminal 1: Start the system
cd /Users/janiceshen/Desktop/Malcolm/Therduce/climate_control
source venv/bin/activate
python3 main.py

# Wait for: "Dashboard available at http://0.0.0.0:5000"

# Browser: Open dashboard
# Go to: http://localhost:5000

# Watch the dashboard update in real-time!

# When done: Press Ctrl+C in terminal to stop
```

---

## ✅ Quick Checklist

Before running:
- [ ] Virtual environment activated (`(venv)` in prompt)
- [ ] In correct directory (`climate_control/`)
- [ ] Dependencies installed (`pip install -r requirements-mac.txt`)

When running:
- [ ] System starts without errors
- [ ] See "Dashboard available" message
- [ ] Browser can access `http://localhost:5000`

---

## 🚀 Ready to Go!

Just run these commands:

```bash
cd /Users/janiceshen/Desktop/Malcolm/Therduce/climate_control
source venv/bin/activate
python3 main.py
```

Then open: **http://localhost:5000** in your browser!

Enjoy your climate control dashboard! 🌡️📊

