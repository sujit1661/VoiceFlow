#!/bin/bash
# Flow Launcher — Linux/macOS
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo -e "${PURPLE}  Flow — AI Voice Dictation by Sujit Sadalage${NC}"
echo -e "${PURPLE}  ============================================${NC}"
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
    echo -e "${RED}[ERROR] Python 3 not found.${NC}"
    echo "  macOS: brew install python3"
    echo "  Linux: sudo apt install python3 python3-pip"
    exit 1
fi

# Check Node / npm
if ! command -v npm &>/dev/null; then
    echo -e "${RED}[ERROR] Node.js / npm not found.${NC}"
    echo "  Install from: https://nodejs.org"
    exit 1
fi

PYTHON=$(command -v python3)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check .env
if [ ! -f "backend/.env" ]; then
    echo -e "${YELLOW}[SETUP] No .env found. Creating from template...${NC}"
    cp backend/.env.example backend/.env
    echo ""
    echo -e "${YELLOW}[ACTION REQUIRED]${NC} Add your Groq API key to backend/.env"
    echo "  Get a FREE key at: https://console.groq.com"
    echo ""
    if command -v nano &>/dev/null; then
        read -rp "Press Enter to open .env in nano..."
        nano backend/.env
    else
        echo "Edit backend/.env before continuing."
        read -rp "Press Enter when done..."
    fi
fi

echo -e "${GREEN}[1/4] Installing backend dependencies...${NC}"
cd backend && $PYTHON -m pip install -r requirements.txt -q --disable-pip-version-check && cd ..

echo -e "${GREEN}[2/4] Installing hotkey service dependencies...${NC}"
cd hotkey_service && $PYTHON -m pip install -r requirements.txt -q --disable-pip-version-check && cd ..

echo -e "${GREEN}[3/4] Installing Electron dependencies...${NC}"
cd electron && npm install --silent && cd ..

echo ""
echo -e "${GREEN}[4/4] Starting everything...${NC}"
echo ""

# Backend
cd backend
$PYTHON -m uvicorn main:app --port 8000 --host 0.0.0.0 &
BACKEND_PID=$!
cd ..
echo -e "${GREEN}[✓] Backend started (PID: $BACKEND_PID)${NC}"
sleep 2

# Hotkey service
cd hotkey_service
$PYTHON service.py &
HOTKEY_PID=$!
cd ..
echo -e "${GREEN}[✓] Hotkey service started (PID: $HOTKEY_PID)${NC}"
sleep 1

# Electron overlay
cd electron
npm start &
ELECTRON_PID=$!
cd ..
echo -e "${GREEN}[✓] Electron overlay started (PID: $ELECTRON_PID)${NC}"

echo ""
echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN}  Flow is running!${NC}"
echo ""
echo -e "  Backend  : ${GREEN}http://localhost:8000${NC}"
echo -e "  API Docs : ${GREEN}http://localhost:8000/docs${NC}"
echo -e "  Overlay  : Electron floating pill (bottom-right)"
echo -e "  Hotkey   : Hold Ctrl anywhere to record"
echo -e "${CYAN}============================================${NC}"
echo ""
echo -e "  Press ${RED}Ctrl+C${NC} to stop everything"
echo ""

# Wait — kill all on Ctrl+C
trap "kill $BACKEND_PID $HOTKEY_PID $ELECTRON_PID 2>/dev/null; echo ''; echo 'Stopped.'" EXIT
wait $BACKEND_PID
