#!/bin/bash
# This script deploys the project to a Raspberry Pi Pico W using mpremote.
# It checks for the Pico W connection, uploads the necessary files, and resets the device.
# Ensure the script is run from the project root directory
# and that mpremote is installed and available in the PATH.
# Usage: ./deploy.sh
# You will need to chmod +x deploy.sh to make it executable.

# Check if mpremote is installed
if ! command -v mpremote &> /dev/null; then
    echo "mpremote could not be found. Please install it first."
    exit 1
fi
# Check if the script is run from the project root directory
if [ ! -f "main.py" ]; then
    echo "This script must be run from the project root directory."
    exit 1
fi

PORT="auto"

echo "Checking Pico-W connection..."

if mpremote connect $PORT exec "print('Connected')" >/dev/null 2>&1; then
    echo "Connected. Uploading files..."

    mpremote connect $PORT fs cp main.py :main.py
    mpremote connect $PORT fs cp local_secrets.py :local_secrets.py

    mpremote connect $PORT reset

    echo "Deploy complete! 🎉"
else
    echo "❌ Pico-W not found. Make sure it is connected."
    exit 1
fi
