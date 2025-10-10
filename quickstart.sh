#!/bin/bash
# Quick start script for CS2 Inventory Tracker

echo "=================================================="
echo "CS2 Inventory Tracker - Quick Start"
echo "=================================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed."
    echo "Please install Python 3.6 or higher."
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"
echo ""

# Check if pip is installed
if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
    echo "Error: pip is not installed."
    echo "Please install pip to manage Python packages."
    exit 1
fi

echo "✓ pip found"
echo ""

# Install dependencies
echo "Installing dependencies..."
if command -v pip3 &> /dev/null; then
    pip3 install -r requirements.txt
else
    pip install -r requirements.txt
fi

if [ $? -ne 0 ]; then
    echo "Error: Failed to install dependencies."
    exit 1
fi

echo ""
echo "✓ Dependencies installed successfully"
echo ""

# Run the demo
echo "=================================================="
echo "Running demo with sample data..."
echo "=================================================="
echo ""
python3 demo_inventory.py

echo ""
echo "=================================================="
echo "Setup complete!"
echo "=================================================="
echo ""
echo "To fetch your own CS2 inventory, run:"
echo "  python3 fetch_inventory.py https://steamcommunity.com/id/YOUR-STEAM-ID/inventory"
echo ""
echo "Make sure your Steam inventory is set to public!"
echo ""
