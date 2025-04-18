#!/bin/bash
# ===================================================
# 🚀 Deploy Script for Raspberry Pi Pico W
# ---------------------------------------------------
# This script checks:
# - mpremote installed
# - main.py exists
# Then:
# - Connects to the Pico W
# - Uploads main.py and local_secrets.py
# - Resets the board
# 
# Usage: ./deploy.sh
# (Remember to chmod +x deploy.sh)
# ===================================================

# --- Colour codes ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Colour

# --- Check for mpremote ---
if ! command -v mpremote &> /dev/null; then
    echo -e "${RED}❌ mpremote could not be found. Please install it first.${NC}"
    exit 1
fi

# --- Check running from project root ---
if [ ! -f "main.py" ]; then
    echo -e "${RED}❌ This script must be run from the project root directory.${NC}"
    exit 1
fi

PORT="auto"

echo -e "${YELLOW}🔍 Checking Pico-W connection...${NC}"

if mpremote connect $PORT exec "print('Connected')" >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Pico-W connected.${NC}"
    echo ""

    echo -e "${BLUE}📤 Uploading files...${NC}"
    mpremote connect $PORT fs cp main.py :main.py
    mpremote connect $PORT fs cp local_secrets.py :local_secrets.py
    echo -e "${GREEN}✅ Files uploaded.${NC}"
    echo ""

    echo -e "${BLUE}🔄 Rebooting device...${NC}"
    mpremote connect $PORT reset
    echo ""

    echo -e "${GREEN}🎉 Deploy complete! Your Unicorn is ready to fly! 🦄${NC}"
else
    echo -e "${RED}❌ Pico-W not found. Please check your USB connection and try again.${NC}"
    exit 1
fi
