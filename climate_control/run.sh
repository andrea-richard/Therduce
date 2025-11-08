#!/bin/bash
# Simple script to run the climate control system
# This ensures the virtual environment is activated

cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "Installing dependencies..."
    source venv/bin/activate
    pip install -r requirements.txt
else
    # Activate virtual environment
    source venv/bin/activate
fi

# Check if we're on Mac or Pi
if [[ "$OSTYPE" == "darwin"* ]]; then
    # Mac - no sudo needed
    echo "🍎 Running on Mac (simulation mode)"
    echo "Starting climate control system..."
    python3 main.py
else
    # Linux (Raspberry Pi) - sudo needed for GPIO
    echo "🍓 Running on Raspberry Pi (hardware mode)"
    echo "Starting climate control system with sudo..."
    sudo -E env "PATH=$PATH" python3 main.py
fi

