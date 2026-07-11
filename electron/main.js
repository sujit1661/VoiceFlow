/**
 * Flow — Electron Overlay
 * Built by Sujit Sadalage
 *
 * Creates a frameless, transparent, always-on-top overlay window
 * that floats bottom-right over whatever window you're typing in.
 * No browser tabs. No address bar. Just the pill.
 */

const { app, BrowserWindow, screen } = require('electron');
const path = require('path');

// Single instance — don't open multiple overlays
if (!app.requestSingleInstanceLock()) {
  app.quit();
  process.exit(0);
}

let overlayWin = null;

function createOverlay() {
  const { width, height } = screen.getPrimaryDisplay().workAreaSize;

  const PILL_W = 340;
  const PILL_H = 80;
  const PAD    = 24;

  overlayWin = new BrowserWindow({
    width:  PILL_W,
    height: PILL_H,
    x: width  - PILL_W - PAD,
    y: height - PILL_H - PAD,

    // Frameless transparent always-on-top
    frame:           false,
    transparent:     true,
    alwaysOnTop:     true,
    resizable:       false,
    skipTaskbar:     true,   // don't appear in taskbar
    focusable:       false,  // don't steal focus from your typing window

    // Keep it above everything including fullscreen apps
    type: process.platform === 'linux' ? 'dock' : undefined,

    webPreferences: {
      nodeIntegration:    false,
      contextIsolation:   true,
      backgroundThrottling: false,
    },
  });

  // Always on top — level "screen-saver" keeps it above fullscreen apps
  overlayWin.setAlwaysOnTop(true, 'screen-saver');
  overlayWin.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: true });

  // Load the overlay HTML
  overlayWin.loadFile(path.join(__dirname, 'overlay.html'));

  // Don't show in alt-tab switcher on Windows
  if (process.platform === 'win32') {
    overlayWin.setSkipTaskbar(true);
  }

  overlayWin.on('closed', () => { overlayWin = null; });
}

app.on('ready', createOverlay);

// Keep the app running even if all windows are closed
app.on('window-all-closed', (e) => e.preventDefault());

// Re-focus second instance → bring overlay back
app.on('second-instance', () => {
  if (!overlayWin) createOverlay();
});
