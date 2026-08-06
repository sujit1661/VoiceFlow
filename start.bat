@echo off
title Flow — Starting...
color 0A

REM ── Always run from the folder this .bat lives in ──────────────────────────
cd /d "%~dp0"
set "ROOT=%~dp0"

echo.
echo  ============================================
echo   Flow — Voice AI by Sujit Sadalage
echo  ============================================
echo.

REM ── Check Python ──────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
  echo  [ERROR] Python not found.
  echo  Install from https://python.org then re-run this file.
  pause
  exit /b 1
)

REM ── Check Node / npm ──────────────────────────
npm --version >nul 2>&1
if errorlevel 1 (
  echo  [ERROR] Node.js not found.
  echo  Install from https://nodejs.org then re-run this file.
  pause
  exit /b 1
)

REM ── Check / create .env ───────────────────────
if not exist "%ROOT%backend\.env" (
  echo  [SETUP] No .env found — creating from template...
  copy "%ROOT%backend\.env.example" "%ROOT%backend\.env" >nul
  echo.
  echo  [ACTION] Add your GROQ_API_KEY to backend\.env
  echo  [ACTION] Get a free key at: https://console.groq.com
  echo.
  notepad "%ROOT%backend\.env"
  echo  Press any key once you have saved your API key...
  pause >nul
)

REM ── Warn if placeholder key still set ─────────
findstr /C:"gsk_your_key_here" "%ROOT%backend\.env" >nul 2>&1
if not errorlevel 1 (
  echo.
  echo  [WARNING] GROQ_API_KEY still has the placeholder value.
  echo  Please edit backend\.env and paste your real key.
  echo.
  notepad "%ROOT%backend\.env"
  echo  Press any key to continue...
  pause >nul
)

echo.
echo  [1/4] Installing backend dependencies...
pip install -r "%ROOT%backend\requirements.txt" -q --disable-pip-version-check
if errorlevel 1 (
  echo  [ERROR] Backend pip install failed.
  pause & exit /b 1
)

echo  [2/4] Installing hotkey service dependencies...
pip install -r "%ROOT%hotkey_service\requirements.txt" -q --disable-pip-version-check
if errorlevel 1 (
  echo  [ERROR] Hotkey service pip install failed.
  pause & exit /b 1
)

echo  [3/4] Installing Electron dependencies...
pushd "%ROOT%electron"
npm install --silent
if errorlevel 1 (
  echo  [ERROR] npm install failed.
  popd & pause & exit /b 1
)
popd

echo.
echo  [4/4] Starting all services...
echo.

REM ── Backend (new window, stays open on error) ──
start "Flow — Backend" cmd /k "cd /d "%ROOT%backend" & python -m uvicorn main:app --host 0.0.0.0 --port 8000"

REM ── Wait for backend to bind ───────────────────
timeout /t 4 /nobreak >nul

REM ── Hotkey service ────────────────────────────
start "Flow — Hotkey Service" cmd /k "cd /d "%ROOT%hotkey_service" & python service.py"

REM ── Electron overlay ──────────────────────────
timeout /t 2 /nobreak >nul
start "Flow — Overlay" cmd /k "cd /d "%ROOT%electron" & npm start"

echo.
echo  ============================================
echo   All services launched!
echo.
echo   Web App  :  http://localhost:8000
echo   API Docs :  http://localhost:8000/docs
echo.
echo   Hotkey   :  Hold Ctrl anywhere to record
echo   Cancel   :  ESC while recording
echo   Quit svc :  Shift+ESC in hotkey service window
echo   Raw mode :  Set FLOW_AUTO_POLISH=false in backend\.env
echo  ============================================
echo.
echo  You can close this window. Services keep running in their own windows.
pause >nul
