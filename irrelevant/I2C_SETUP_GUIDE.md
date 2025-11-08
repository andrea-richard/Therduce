# I2C Setup Guide for Raspberry Pi
## Enabling I2C for SHT35-DIS-B Sensor

---

## What is `sudo raspi-config`?

**`raspi-config`** is a built-in configuration tool for Raspberry Pi OS. It's a text-based menu system that lets you configure various hardware interfaces and system settings without editing configuration files manually.

### Why use `sudo`?
- `sudo` means "Super User Do" - it runs the command with administrator privileges
- `raspi-config` needs root access to modify system settings
- On Raspberry Pi, you typically need `sudo` for hardware configuration

### What does it do?
`raspi-config` provides an easy menu-driven interface to:
- Enable/disable hardware interfaces (I2C, SPI, Serial, etc.)
- Change system settings (hostname, password, locale)
- Overclock the CPU
- Set boot options
- Update the tool itself

---

## How to Enable I2C

### Method 1: Using `raspi-config` (Recommended - Easiest)

**Step-by-step:**

1. **Open a terminal** on your Raspberry Pi (or SSH into it)

2. **Run the command:**
   ```bash
   sudo raspi-config
   ```

3. **Navigate the menu:**
   - Use **arrow keys** (↑↓) to move up/down
   - Press **Enter** to select
   - Press **Tab** to move between OK/Cancel buttons
   - Press **Esc** to go back

4. **Enable I2C:**
   ```
   Main Menu
   └── 3 Interface Options
       └── I5 I2C
           └── <Yes> (Enable I2C interface)
   ```

5. **Exit and reboot:**
   - Press **Tab** to select "Finish"
   - Press **Enter**
   - When asked to reboot, select **Yes**

6. **After reboot, verify I2C is enabled:**
   ```bash
   ls /dev/i2c-*
   # Should show: /dev/i2c-1
   ```

### Method 2: Manual Configuration (Alternative)

If `raspi-config` doesn't work or you prefer manual setup:

1. **Edit the boot configuration:**
   ```bash
   sudo nano /boot/config.txt
   ```

2. **Add or uncomment this line:**
   ```
   dtparam=i2c_arm=on
   ```
   (If it's already there with `#` in front, remove the `#`)

3. **Save and exit:**
   - Press `Ctrl+X`
   - Press `Y` to confirm
   - Press `Enter` to save

4. **Reboot:**
   ```bash
   sudo reboot
   ```

5. **Verify:**
   ```bash
   ls /dev/i2c-*
   # Should show: /dev/i2c-1
   ```

---

## Visual Guide: Using raspi-config

When you run `sudo raspi-config`, you'll see a menu like this:

```
┌─────────────────────────────────────────────────────────┐
│  Raspberry Pi Software Configuration Tool (raspi-config)│
├─────────────────────────────────────────────────────────┤
│                                                           │
│  1 System Options      Configure system settings        │
│  2 Display Options     Configure display settings       │
│  3 Interface Options   Configure connections to peripherals│
│  4 Performance Options Configure performance settings   │
│  5 Localisation Options Configure language and regional │
│  6 Advanced Options     Configure advanced settings     │
│  7 Update               Update this tool                    │
│  8 About raspi-config   Information about this tool      │
│                                                           │
│                    <Select>    <Finish>                   │
└─────────────────────────────────────────────────────────┘
```

**Select option 3** (Interface Options), then you'll see:

```
┌─────────────────────────────────────────────────────────┐
│  Configure connections to peripherals                     │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  P1 Camera      Enable/Disable connection to the Camera │
│  P2 SSH          Enable/Disable remote command line access│
│  P3 VNC          Enable/Disable graphical remote access  │
│  P4 SPI          Enable/Disable automatic loading of SPI │
│  P5 I2C          Enable/Disable automatic loading of I2C│
│  P6 Serial Port  Enable/Disable shell and kernel messages│
│  P7 1-Wire       Enable/Disable one-wire interface       │
│  P8 Remote GPIO  Enable/Disable remote access to GPIO    │
│                                                           │
│                    <Select>    <Back>                     │
└─────────────────────────────────────────────────────────┘
```

**Select option P5** (I2C), then you'll see:

```
┌─────────────────────────────────────────────────────────┐
│  Would you like the ARM I2C interface to be enabled?    │
│                                                           │
│  The ARM I2C interface allows you to connect hardware  │
│  devices to your Raspberry Pi using the I2C protocol.  │
│                                                           │
│                    <Yes>    <No>                         │
└─────────────────────────────────────────────────────────┘
```

**Select <Yes>**, then you'll be asked to reboot.

---

## Why Do We Need I2C?

**I2C** (Inter-Integrated Circuit) is a communication protocol that allows multiple devices to communicate over just 2 wires:
- **SDA** (Serial Data) - GPIO 2
- **SCL** (Serial Clock) - GPIO 3

### For Your Climate Control System:

The **SHT35-DIS-B sensor** uses I2C to communicate with the Raspberry Pi. Without I2C enabled:
- ❌ The sensor cannot be detected
- ❌ No temperature/humidity readings
- ❌ System will run in simulation mode only

### I2C Benefits:
- **Simple wiring** - Only 2 data wires + power + ground
- **Multiple devices** - Can connect many sensors on same bus
- **Low speed but reliable** - Perfect for sensors
- **Built into Raspberry Pi** - No extra hardware needed

---

## Verifying I2C is Working

### Test 1: Check if I2C device exists
```bash
ls /dev/i2c-*
```
**Expected output:**
```
/dev/i2c-1
```

### Test 2: Check if I2C tools are installed
```bash
sudo apt-get install i2c-tools
```

### Test 3: Scan for I2C devices
```bash
sudo i2cdetect -y 1
```

**Expected output** (if SHT35-DIS-B is connected):
```
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
00:                         -- -- -- -- -- -- -- -- 
10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
20: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
30: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
40: 44 -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
50: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
60: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
70: -- -- -- -- -- -- -- --
```

The **44** (or **45**) shows your SHT35-DIS-B sensor is detected at I2C address 0x44 (or 0x45).

### Test 4: Test with your Python code
```bash
cd climate_control
python3 -c "from sensors import SHT35Sensor; s = SHT35Sensor(); print(s.read())"
```

**Expected output:**
```
(5.2, 89.5)  # (temperature, humidity)
```

---

## Troubleshooting

### Problem: "Permission denied" when accessing I2C

**Solution:** Add your user to the `i2c` group:
```bash
sudo usermod -a -G i2c $USER
# Log out and log back in, or:
newgrp i2c
```

### Problem: I2C device not found (`/dev/i2c-1` doesn't exist)

**Solutions:**
1. Make sure you rebooted after enabling I2C
2. Check if I2C is enabled:
   ```bash
   cat /boot/config.txt | grep i2c
   # Should show: dtparam=i2c_arm=on
   ```
3. Try enabling manually (Method 2 above)

### Problem: Sensor not detected in `i2cdetect`

**Check:**
1. **Wiring:**
   - SDA → GPIO 2 (Pin 3)
   - SCL → GPIO 3 (Pin 5)
   - VCC → 3.3V (Pin 1)
   - GND → Ground (Pin 6)

2. **Power:** Sensor needs 3.3V (not 5V!)

3. **Pull-up resistors:** SHT35-DIS-B should have built-in pull-ups, but if not, add 4.7kΩ resistors on SDA and SCL to 3.3V

4. **I2C address:** Check if your sensor uses 0x44 or 0x45 (some boards have a jumper)

### Problem: "No module named 'smbus2'"

**Solution:** Install the Python package:
```bash
pip install smbus2
# or
pip install -r requirements.txt
```

---

## Quick Reference

### Enable I2C:
```bash
sudo raspi-config
# Navigate: 3 → P5 → Yes → Reboot
```

### Check I2C status:
```bash
ls /dev/i2c-*          # Should show /dev/i2c-1
sudo i2cdetect -y 1    # Scan for devices
```

### Test sensor:
```bash
python3 -c "from sensors import SHT35Sensor; s = SHT35Sensor(); print(s.read())"
```

### If I2C not working:
- System will automatically use **simulation mode**
- Dashboard will still work
- Perfect for demo without hardware!

---

## For Hackathon Demo

**Good news:** If you can't get I2C working or don't have the sensor connected, the system automatically detects this and runs in **simulation mode**:

- ✅ All features work
- ✅ Dashboard shows realistic data
- ✅ AI control logic works perfectly
- ✅ Perfect for demonstrating the system!

The code in `sensors.py` checks if I2C is available and falls back to simulation automatically.

---

## Summary

1. **`raspi-config`** = Raspberry Pi configuration tool (menu-driven)
2. **I2C** = Communication protocol for sensors (2 wires)
3. **Enable it:** `sudo raspi-config` → Interface Options → I2C → Yes → Reboot
4. **Verify:** `ls /dev/i2c-*` should show `/dev/i2c-1`
5. **Test:** `sudo i2cdetect -y 1` should show your sensor (0x44 or 0x45)

**If it doesn't work:** Don't worry! The system runs in simulation mode automatically, so your demo will still be perfect! 🎯

