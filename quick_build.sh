#!/bin/bash
# Quick build script for Linux/Mac

echo "Building ProtectSecure..."
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    exit 1
fi

# Install dependencies if needed
echo "Installing/updating dependencies..."
pip3 install -r requirements.txt

# Run build
echo ""
echo "Starting build process..."
python3 build.py

echo ""
echo "Build complete!"
