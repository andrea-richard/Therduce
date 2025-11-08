# Running the Climate Control System

## ⚠️ Important: Don't Use `sudo` on Mac!

### The Problem

When you run `sudo python3 main.py`, you're running Python as the **root user**, which:
- ❌ Doesn't use your virtual environment
- ❌ Can't find packages installed in `venv/`
- ❌ Causes `ModuleNotFoundError: No module named 'yaml'`

### The Solution

**On Mac, you don't need `sudo`!** GPIO is mocked, so no special permissions are needed.

---

## ✅ Correct Way to Run (Mac)

### Step 1: Activate Virtual Environment

```bash
cd climate_control
source venv/bin/activate
```

You should see `(venv)` in your prompt.

### Step 2: Run the System

```bash
python3 main.py
```

**NOT** `sudo python3 main.py` ❌

### Step 3: Access Dashboard

Open your browser:
```
http://localhost:5000
```

---

## 🔧 If You Get "ModuleNotFoundError"

### Problem: Packages not installed

**Solution:** Install dependencies in your virtual environment:

```bash
cd climate_control
source venv/bin/activate  # Make sure venv is active!
pip install -r requirements.txt
```

### Problem: Running with `sudo`

**Solution:** Don't use `sudo` on Mac:

```bash
# ❌ WRONG:
sudo python3 main.py

# ✅ CORRECT:
source venv/bin/activate
python3 main.py
```

### Problem: Virtual environment not activated

**Check:** Look for `(venv)` in your terminal prompt. If you don't see it:

```bash
source venv/bin/activate
```

---

## 🍎 Mac vs 🍓 Raspberry Pi

### On Mac (Development):

```bash
# No sudo needed!
cd climate_control
source venv/bin/activate
python3 main.py
```

- GPIO is mocked (simulated)
- No special permissions needed
- Perfect for development and demo

### On Raspberry Pi (Production):

```bash
# Sudo IS needed for GPIO access
cd climate_control
source venv/bin/activate
sudo python3 main.py
```

- Real GPIO hardware requires root access
- But still use venv! (activate it first, then sudo)

---

## 🎯 Quick Start Commands

### First Time Setup:

```bash
cd climate_control

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install packages
pip install -r requirements.txt

# Run the system
python3 main.py
```

### Every Time You Run:

```bash
cd climate_control
source venv/bin/activate
python3 main.py
```

---

## 🐛 Common Errors & Fixes

### Error: `ModuleNotFoundError: No module named 'yaml'`

**Cause:** Virtual environment not activated, or packages not installed

**Fix:**
```bash
source venv/bin/activate
pip install -r requirements.txt
python3 main.py  # WITHOUT sudo
```

### Error: `Permission denied`

**On Mac:** You shouldn't get this. If you do, check file permissions:
```bash
chmod +x main.py
```

**On Pi:** Use `sudo` (but activate venv first):
```bash
source venv/bin/activate
sudo python3 main.py
```

### Error: `Address already in use` (port 5000)

**Cause:** Dashboard already running

**Fix:** 
- Find and kill the process: `lsof -ti:5000 | xargs kill`
- Or use a different port in `config.yaml`

---

## 📋 Complete Workflow

### Development on Mac:

```bash
# 1. Navigate to project
cd /Users/janiceshen/Desktop/Malcolm/Therduce/climate_control

# 2. Activate virtual environment
source venv/bin/activate

# 3. (First time only) Install dependencies
pip install -r requirements.txt

# 4. Run the system
python3 main.py

# 5. Open dashboard in browser
# http://localhost:5000
```

### Production on Raspberry Pi:

```bash
# 1. SSH into Pi
ssh pi@raspberrypi.local

# 2. Navigate to project
cd ~/climate_control

# 3. Activate virtual environment
source venv/bin/activate

# 4. Run with sudo (for GPIO access)
sudo python3 main.py

# 5. Access dashboard from any device on network
# http://raspberrypi.local:5000
```

---

## 💡 Pro Tips

1. **Always activate venv first** - Look for `(venv)` in prompt
2. **On Mac: No sudo needed** - GPIO is mocked
3. **On Pi: Activate venv THEN sudo** - `source venv/bin/activate && sudo python3 main.py`
4. **Check if running:** `ps aux | grep main.py`
5. **Stop the system:** Press `Ctrl+C` in the terminal

---

## 🎯 For Your Current Situation

You're on Mac, so:

```bash
cd climate_control
source venv/bin/activate  # Make sure you see (venv)
python3 main.py           # NO sudo!
```

Then open: `http://localhost:5000`

That's it! 🚀

