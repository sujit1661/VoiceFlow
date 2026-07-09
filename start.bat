@echo off
title Flow — Starting...
color 0A

echo.
echo  ============================================
echo   Flow — Voice AI by Sujit Sadalage
echo  ============================================
echo.

REM ── Check .env ────────────────────────────────
if not exist "backend\.env" (
  echo  [SETUP] Creating .env from example...
  copy "backend\.env.example" "backend\.env" >nul
  echo  [SETUP] Add your GROQ_API_KEY to backend\.env
  echo  [SETUP] Get a free key at: https://console.groq.com
  echo.
  notepad "backend\.env"
  echo  Press any key after saving your API key...
  pause >nul
)

REM ── Install backend deps ───────────────────────
echo  [1/3] Installing backend dependencies...
cd backend
pip install -r requirements.txt -q
cd ..

REM ── Install hotkey service deps ────────────────
echo  [2/3] Installing hotkey service dependencies...
cd hotkey_service
pip install -r requirements.txt -q
cd ..

echo.
echo  [3/3] Starting everything...
echo.

REM ── Start backend in a new window ─────────────
start "Flow Backend" cmd /k "cd backend && uvicorn main:app --host 0.0.0.0 --port 8000"

REM ── Wait for backend to be ready ──────────────
timeout /t 3 /nobreak >nul

REM ── Start hotkey service in a new window ──────
start "Flow Hotkey Service" cmd /k "cd hotkey_service && python service.py"

REM ── Open browser ──────────────────────────────
timeout /t 2 /nobreak >nul
start "" "http://localhost:8000"

echo.
echo  ============================================
echo   Everything is running!
echo.
echo   Web App  :  http://localhost:8000
echo   Backend  :  http://localhost:8000/health
echo   API Docs :  http://localhost:8000/docs
echo.
echo   Global hotkey: Hold Ctrl anywhere to record
echo   Works in: Gmail, Slack, VS Code, Notepad...
echo  ============================================
echo.
pause
