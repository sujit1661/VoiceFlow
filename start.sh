#!/bin/bash
# VoiceFlow Launcher — Linux/macOS

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo ""
echo -e "${PURPLE}  VoiceFlow — AI-Powered Voice Dictation${NC}"
echo -e "${PURPLE}  ======================================${NC}"
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
    echo -e "${RED}[ERROR] Python 3 not found. Install it with:${NC}"
    echo "  macOS: brew install python3"
    echo "  Linux: sudo apt install python3 python3-pip"
    exit 1
fi

PYTHON=$(command -v python3)
echo -e "${GREEN}[✓] Python: $($PYTHON --version)${NC}"

# Go to script directory
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
    echo -e "  Edit the file: ${CYAN}nano backend/.env${NC}"
    echo ""

    # Try to open in editor
    if command -v nano &>/dev/null; then
        read -rp "Press Enter to open .env in nano (Ctrl+X to save and exit)..."
        nano backend/.env
    else
        echo "Please edit backend/.env before continuing."
        read -rp "Press Enter when done..."
    fi
fi

echo -e "${GREEN}[1/3] Installing backend dependencies...${NC}"
cd backend
$PYTHON -m pip install -r requirements.txt -q --disable-pip-version-check
cd ..
echo -e "${GREEN}[✓] Dependencies installed${NC}"

echo ""
echo -e "${GREEN}[2/3] Starting FastAPI backend on http://localhost:8000 ...${NC}"
cd backend
$PYTHON -m uvicorn main:app --reload --port 8000 --host 0.0.0.0 &
BACKEND_PID=$!
cd ..
echo -e "${GREEN}[✓] Backend started (PID: $BACKEND_PID)${NC}"

echo ""
echo -e "${GREEN}[3/3] Waiting for backend to start...${NC}"
sleep 2

# Open browser
echo -e "${GREEN}[✓] Opening VoiceFlow in browser...${NC}"
FRONTEND_PATH="$SCRIPT_DIR/frontend/index.html"

if command -v open &>/dev/null; then
    open "$FRONTEND_PATH"          # macOS
elif command -v xdg-open &>/dev/null; then
    xdg-open "$FRONTEND_PATH"      # Linux
elif command -v wslview &>/dev/null; then
    wslview "$FRONTEND_PATH"       # WSL
else
    echo -e "${YELLOW}[!] Could not auto-open browser. Open manually:${NC}"
    echo "    file://$FRONTEND_PATH"
fi

echo ""
echo -e "${CYAN}================================================${NC}"
echo -e "${CYAN}  VoiceFlow is running!${NC}"
echo ""
echo -e "  Web App:  file://$FRONTEND_PATH"
echo -e "  Backend:  ${GREEN}http://localhost:8000${NC}"
echo -e "  API Docs: ${GREEN}http://localhost:8000/docs${NC}"
echo -e "${CYAN}================================================${NC}"
echo ""
echo -e "${YELLOW}  Global hotkey service (auto-types anywhere):${NC}"
echo "  cd hotkey_service"
echo "  pip3 install -r requirements.txt"
echo "  python3 service.py"
echo "  (Hold RIGHT CTRL to record)"
echo ""
echo -e "  Press ${RED}Ctrl+C${NC} to stop the backend"
echo ""

# Wait for backend
wait $BACKEND_PID
