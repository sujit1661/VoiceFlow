/**
 * VoiceFlow App — Main JavaScript
 * Handles: recording, transcription, AI polishing, UI state, history, settings
 */

// ── State ──────────────────────────────────────────────────────────────────
// Auto-detect API URL: if served from FastAPI backend, use same origin
function detectApiUrl() {
  const saved = localStorage.getItem('vf_apiUrl');
  if (saved) return saved;
  // If page is opened from file:// use localhost
  if (window.location.protocol === 'file:') return 'http://localhost:8000';
  // If served by FastAPI, use same origin
  return window.location.origin;
}

const state = {
  isRecording: false,
  isProcessing: false,
  mediaRecorder: null,
  audioChunks: [],
  ctrlDown: false,
  timerInterval: null,
  timerSeconds: 0,
  ws: null,
  wsConnected: false,
  apiUrl: detectApiUrl(),
  autoPolish: localStorage.getItem('vf_autoPolish') !== 'false',
  polishMode: localStorage.getItem('vf_polishMode') || 'websocket',
  history: JSON.parse(localStorage.getItem('vf_history') || '[]'),
};

// ── DOM refs ───────────────────────────────────────────────────────────────
const $ = id => document.getElementById(id);
const micBtn          = $('micBtn');
const micIcon         = $('micIcon');
const statusBadge     = $('statusBadge');
const statusDot       = $('statusDot');
const statusText      = $('statusText');
const waveform        = $('waveform');
const outputText      = $('outputText');
const rawText         = $('rawText');
const rawSection      = $('rawSection');
const polishedBadge   = $('polishedBadge');
const processingSpinner = $('processingSpinner');
const copyBtn         = $('copyBtn');
const clearBtn        = $('clearBtn');
const charCount       = $('charCount');
const errorMsg        = $('errorMsg');
const contextSelect   = $('contextSelect');
const historyList     = $('historyList');
const settingsBtn     = $('settingsBtn');
const settingsPanel   = $('settingsPanel');
const settingsOverlay = $('settingsOverlay');
const closeSettings   = $('closeSettings');
const apiUrlInput     = $('apiUrlInput');
const defaultContextSelect = $('defaultContextSelect');
const autoPolishToggle = $('autoPolishToggle');
const toggleTrack     = $('toggleTrack');
const toggleThumb     = $('toggleThumb');
const recRing1        = $('recRing1');
const recRing2        = $('recRing2');
const testConnection  = $('testConnection');
const connectionResult = $('connectionResult');
const clearHistoryBtn = $('clearHistoryBtn');
const recTimer        = $('recTimer');
const timerDisplay    = $('timerDisplay');
const backendDot      = $('backendDot');
const backendStatus   = $('backendStatus');
const toast           = $('toast');
const toastMsg        = $('toastMsg');
const toastIcon       = $('toastIcon');

// ── Init ───────────────────────────────────────────────────────────────────
function init() {
  loadSettings();
  renderHistory();
  checkBackend();
  setupEventListeners();
  setInterval(checkBackend, 15000);
}

function loadSettings() {
  apiUrlInput.value = state.apiUrl;
  autoPolishToggle.checked = state.autoPolish;
  updateToggleUI(state.autoPolish);
  const savedContext = localStorage.getItem('vf_context') || 'general';
  contextSelect.value = savedContext;
  defaultContextSelect.value = savedContext;
  document.querySelectorAll('input[name="polishMode"]').forEach(r => {
    r.checked = r.value === state.polishMode;
  });
}

// ── Event listeners ────────────────────────────────────────────────────────
function setupEventListeners() {
  // Mic button click toggle
  micBtn.addEventListener('mousedown', () => { if (!state.isProcessing) startRecording(); });
  micBtn.addEventListener('mouseup',   () => { if (state.isRecording)   stopRecording(); });
  micBtn.addEventListener('mouseleave',() => { if (state.isRecording)   stopRecording(); });
  micBtn.addEventListener('touchstart', e => { e.preventDefault(); if (!state.isProcessing) startRecording(); });
  micBtn.addEventListener('touchend',   e => { e.preventDefault(); if (state.isRecording) stopRecording(); });

  // Ctrl key global
  document.addEventListener('keydown', e => {
    if ((e.key === 'Control') && !state.ctrlDown && !state.isProcessing) {
      state.ctrlDown = true;
      if (!state.isRecording) startRecording();
    }
    if (e.key === 'Escape') { clearOutput(); }
  });
  document.addEventListener('keyup', e => {
    if (e.key === 'Control') {
      state.ctrlDown = false;
      if (state.isRecording) stopRecording();
    }
  });

  // Copy
  copyBtn.addEventListener('click', copyToClipboard);

  // Clear
  clearBtn.addEventListener('click', clearOutput);

  // Char count
  outputText.addEventListener('input', updateCharCount);

  // Context save
  contextSelect.addEventListener('change', () => {
    localStorage.setItem('vf_context', contextSelect.value);
  });

  // Settings
  settingsBtn.addEventListener('click', openSettings);
  closeSettings.addEventListener('click', closeSettingsPanel);
  settingsOverlay.addEventListener('click', closeSettingsPanel);

  apiUrlInput.addEventListener('change', () => {
    state.apiUrl = apiUrlInput.value.trim();
    localStorage.setItem('vf_apiUrl', state.apiUrl);
    state.wsConnected = false;
    if (state.ws) { state.ws.close(); state.ws = null; }
  });

  defaultContextSelect.addEventListener('change', () => {
    contextSelect.value = defaultContextSelect.value;
    localStorage.setItem('vf_context', defaultContextSelect.value);
  });

  autoPolishToggle.addEventListener('change', () => {
    state.autoPolish = autoPolishToggle.checked;
    localStorage.setItem('vf_autoPolish', state.autoPolish);
    updateToggleUI(state.autoPolish);
  });

  toggleTrack.addEventListener('click', () => {
    autoPolishToggle.checked = !autoPolishToggle.checked;
    autoPolishToggle.dispatchEvent(new Event('change'));
  });

  document.querySelectorAll('input[name="polishMode"]').forEach(r => {
    r.addEventListener('change', () => {
      state.polishMode = r.value;
      localStorage.setItem('vf_polishMode', r.value);
      if (state.ws) { state.ws.close(); state.ws = null; state.wsConnected = false; }
    });
  });

  testConnection.addEventListener('click', async () => {
    testConnection.textContent = 'Testing...';
    testConnection.disabled = true;
    try {
      const r = await fetch(`${state.apiUrl}/health`, { signal: AbortSignal.timeout(4000) });
      const d = await r.json();
      connectionResult.style.display = 'block';
      connectionResult.style.color = '#7a9e6e';
      connectionResult.textContent = `✓ Connected — ${d.message}`;
    } catch {
      connectionResult.style.display = 'block';
      connectionResult.style.color = '#c97a6a';
      connectionResult.textContent = '✗ Cannot reach backend. Is it running on port 8000?';
    }
    testConnection.textContent = 'Test Connection';
    testConnection.disabled = false;
  });

  clearHistoryBtn.addEventListener('click', () => {
    state.history = [];
    localStorage.setItem('vf_history', '[]');
    renderHistory();
  });
}

// ── Recording ──────────────────────────────────────────────────────────────
async function startRecording() {
  if (state.isRecording || state.isProcessing) return;

  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    state.audioChunks = [];

    // Prefer webm/opus, fallback to default
    const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
      ? 'audio/webm;codecs=opus'
      : MediaRecorder.isTypeSupported('audio/webm')
        ? 'audio/webm'
        : '';

    state.mediaRecorder = new MediaRecorder(stream, mimeType ? { mimeType } : {});
    state.mediaRecorder.ondataavailable = e => {
      if (e.data.size > 0) state.audioChunks.push(e.data);
    };
    state.mediaRecorder.onstop = handleRecordingStop;
    state.mediaRecorder.start(100); // collect every 100ms

    state.isRecording = true;
    setUIRecording();
    startTimer();

  } catch (err) {
    showError('Microphone access denied. Please allow microphone permissions.');
    console.error('Microphone error:', err);
  }
}

function stopRecording() {
  if (!state.isRecording || !state.mediaRecorder) return;
  state.isRecording = false;
  state.mediaRecorder.stop();
  state.mediaRecorder.stream.getTracks().forEach(t => t.stop());
  stopTimer();
  setUIProcessing();
}

async function handleRecordingStop() {
  if (state.audioChunks.length === 0) {
    setUIIdle();
    return;
  }

  const mimeType = state.mediaRecorder.mimeType || 'audio/webm';
  const blob = new Blob(state.audioChunks, { type: mimeType });

  // Need at least ~0.5 seconds of audio
  if (blob.size < 1000) {
    setUIIdle();
    showError('Recording too short. Try holding the key a bit longer.');
    return;
  }

  await transcribeAudio(blob, mimeType);
}

// ── Transcription ──────────────────────────────────────────────────────────
async function transcribeAudio(blob, mimeType) {
  setUIProcessing('Transcribing...');
  hideError();

  try {
    const formData = new FormData();
    const ext = mimeType.includes('webm') ? 'webm' : mimeType.includes('ogg') ? 'ogg' : 'wav';
    formData.append('audio', blob, `recording.${ext}`);

    const res = await fetch(`${state.apiUrl}/api/transcribe`, {
      method: 'POST',
      body: formData,
      signal: AbortSignal.timeout(30000),
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    if (!data.success) throw new Error(data.error || 'Transcription failed');

    const rawTranscript = (data.text || '').trim();
    if (!rawTranscript) {
      showError('No speech detected. Try speaking louder or longer.');
      setUIIdle();
      return;
    }

    showRawTranscript(rawTranscript);

    if (state.autoPolish) {
      await polishText(rawTranscript);
    } else {
      outputText.value = rawTranscript;
      updateCharCount();
      copyBtn.style.display = '';
      setUIIdle('Done');
      addToHistory(rawTranscript, rawTranscript);
    }

  } catch (err) {
    console.error('Transcription error:', err);
    if (err.name === 'TimeoutError') {
      showError('Request timed out. Is the backend running?');
    } else if (err.message.includes('fetch')) {
      showError('Cannot reach backend. Start the server with: uvicorn main:app --reload');
    } else {
      showError(`Transcription error: ${err.message}`);
    }
    setUIIdle();
  }
}

// ── Polish ─────────────────────────────────────────────────────────────────
async function polishText(rawTranscript) {
  setUIProcessing('Polishing with AI...');
  processingSpinner.style.display = '';

  const context = contextSelect.value;

  if (state.polishMode === 'websocket') {
    await polishViaWebSocket(rawTranscript, context);
  } else {
    await polishViaRest(rawTranscript, context);
  }
}

async function polishViaRest(rawTranscript, context) {
  try {
    const formData = new FormData();
    formData.append('text', rawTranscript);
    formData.append('context', context);

    const res = await fetch(`${state.apiUrl}/api/polish`, {
      method: 'POST',
      body: formData,
      signal: AbortSignal.timeout(30000),
    });

    const data = await res.json();
    if (!data.success) throw new Error(data.error || 'Polishing failed');

    const polished = (data.polished || rawTranscript).trim();
    outputText.value = polished;
    updateCharCount();
    showPolishedBadge();
    copyBtn.style.display = '';
    setUIIdle('Done ✨');
    addToHistory(rawTranscript, polished);
    showToast('✨ Text polished!', '✨');

  } catch (err) {
    console.error('Polish error:', err);
    // Fallback: show raw
    outputText.value = rawTranscript;
    updateCharCount();
    copyBtn.style.display = '';
    showError(`Polish failed: ${err.message}. Showing raw transcript.`);
    setUIIdle();
    addToHistory(rawTranscript, rawTranscript);
  } finally {
    processingSpinner.style.display = 'none';
  }
}

async function polishViaWebSocket(rawTranscript, context) {
  return new Promise((resolve) => {
    try {
      const wsUrl = state.apiUrl.replace('http://', 'ws://').replace('https://', 'wss://');
      const ws = new WebSocket(`${wsUrl}/ws/stream`);
      let fullText = '';
      let streamStarted = false;

      ws.onopen = () => {
        ws.send(JSON.stringify({ text: rawTranscript, context }));
      };

      ws.onmessage = e => {
        const msg = JSON.parse(e.data);

        if (msg.type === 'start') {
          streamStarted = true;
          outputText.value = '';
          setUIProcessing('AI writing...');
        } else if (msg.type === 'token') {
          fullText += msg.token;
          outputText.value = fullText;
          outputText.classList.add('typing-cursor');
          updateCharCount();
          // Auto-scroll textarea
          outputText.scrollTop = outputText.scrollHeight;
        } else if (msg.type === 'done') {
          outputText.classList.remove('typing-cursor');
          const finalText = (msg.full_text || fullText).trim();
          outputText.value = finalText;
          updateCharCount();
          showPolishedBadge();
          copyBtn.style.display = '';
          setUIIdle('Done ✨');
          addToHistory(rawTranscript, finalText);
          showToast('✨ Text polished!', '✨');
          processingSpinner.style.display = 'none';
          ws.close();
          resolve();
        } else if (msg.type === 'error') {
          throw new Error(msg.message);
        }
      };

      ws.onerror = () => {
        // Fallback to REST
        console.warn('WebSocket failed, falling back to REST');
        ws.close();
        polishViaRest(rawTranscript, context).then(resolve);
      };

      ws.onclose = () => {
        if (!streamStarted) {
          // WS never connected properly, use REST
          polishViaRest(rawTranscript, context).then(resolve);
        } else {
          resolve();
        }
      };

      // Timeout
      setTimeout(() => {
        if (ws.readyState !== WebSocket.CLOSED) {
          ws.close();
          if (!streamStarted) {
            polishViaRest(rawTranscript, context).then(resolve);
          }
        }
      }, 30000);

    } catch (err) {
      console.error('WebSocket error:', err);
      polishViaRest(rawTranscript, context).then(resolve);
    }
  });
}

// ── UI State management ────────────────────────────────────────────────────
function setUIIdle(msg = 'Press & hold Ctrl to record') {
  state.isProcessing = false;
  micBtn.disabled = false;
  micBtn.classList.remove('recording');
  waveform.classList.remove('active');
  recTimer.style.display = 'none';
  if (recRing1) recRing1.style.display = 'none';
  if (recRing2) recRing2.style.display = 'none';

  statusBadge.className = 'status-badge status-idle';
  statusDot.classList.remove('animate');
  statusText.textContent = msg;
}

function setUIRecording() {
  state.isProcessing = false;
  micBtn.classList.add('recording');
  waveform.classList.add('active');
  recTimer.style.display = '';
  if (recRing1) recRing1.style.display = '';
  if (recRing2) recRing2.style.display = '';

  statusBadge.className = 'status-badge status-recording';
  statusDot.classList.add('animate');
  statusText.textContent = 'Recording...';
}

function setUIProcessing(msg = 'Processing...') {
  state.isProcessing = true;
  micBtn.classList.remove('recording');
  waveform.classList.remove('active');
  recTimer.style.display = 'none';

  statusBadge.className = 'status-badge status-processing';
  statusDot.classList.add('animate');
  statusText.textContent = msg;
}

// ── Timer ──────────────────────────────────────────────────────────────────
function startTimer() {
  state.timerSeconds = 0;
  timerDisplay.textContent = '00:00';
  recTimer.style.display = '';
  state.timerInterval = setInterval(() => {
    state.timerSeconds++;
    const m = String(Math.floor(state.timerSeconds / 60)).padStart(2, '0');
    const s = String(state.timerSeconds % 60).padStart(2, '0');
    timerDisplay.textContent = `${m}:${s}`;
  }, 1000);
}

function stopTimer() {
  clearInterval(state.timerInterval);
}

// ── Output helpers ─────────────────────────────────────────────────────────
function showRawTranscript(text) {
  rawSection.style.display = '';
  rawText.textContent = text;
  rawText.classList.add('text-appear');
}

function showPolishedBadge() {
  polishedBadge.style.display = '';
  polishedBadge.classList.add('text-appear');
}

function updateCharCount() {
  const len = outputText.value.length;
  charCount.textContent = `${len} character${len !== 1 ? 's' : ''}`;
  outputText.classList.toggle('has-content', len > 0);
}

function showError(msg) {
  errorMsg.textContent = msg;
  errorMsg.style.display = '';
}

function hideError() {
  errorMsg.style.display = 'none';
}

function clearOutput() {
  outputText.value = '';
  rawSection.style.display = 'none';
  rawText.textContent = '';
  polishedBadge.style.display = 'none';
  copyBtn.style.display = 'none';
  updateCharCount();
  hideError();
  setUIIdle();
}

// ── Copy ───────────────────────────────────────────────────────────────────
function copyToClipboard() {
  const text = outputText.value;
  if (!text) return;
  navigator.clipboard.writeText(text).then(() => {
    showToast('Copied to clipboard!', '✓');
  }).catch(() => {
    // Fallback
    outputText.select();
    document.execCommand('copy');
    showToast('Copied!', '✓');
  });
}

// ── Toast ──────────────────────────────────────────────────────────────────
let toastTimer = null;
function showToast(msg, icon = '✓') {
  toastMsg.textContent = msg;
  toastIcon.textContent = icon;
  toast.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove('show'), 2500);
}

// ── History ────────────────────────────────────────────────────────────────
function addToHistory(raw, polished) {
  const item = {
    id: Date.now(),
    raw,
    polished,
    context: contextSelect.value,
    time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
  };
  state.history.unshift(item);
  if (state.history.length > 10) state.history.pop();
  localStorage.setItem('vf_history', JSON.stringify(state.history));
  renderHistory();
}

function renderHistory() {
  if (state.history.length === 0) {
    historyList.innerHTML = '<p class="text-gray-600 text-xs text-center py-4">No recordings yet</p>';
    return;
  }
  historyList.innerHTML = state.history.map(item => `
    <div class="history-item" onclick="loadHistoryItem(${item.id})" title="${escapeHtml(item.polished)}">
      <div class="flex items-center justify-between mb-0.5">
        <span class="text-purple-400 text-xs">${item.context}</span>
        <span class="text-gray-700 text-xs">${item.time}</span>
      </div>
      <div class="text-gray-400 text-xs truncate">${escapeHtml(item.polished.slice(0, 80))}${item.polished.length > 80 ? '…' : ''}</div>
    </div>
  `).join('');
}

function loadHistoryItem(id) {
  const item = state.history.find(h => h.id === id);
  if (!item) return;
  outputText.value = item.polished;
  if (item.raw !== item.polished) {
    rawSection.style.display = '';
    rawText.textContent = item.raw;
    polishedBadge.style.display = '';
  }
  contextSelect.value = item.context;
  copyBtn.style.display = '';
  updateCharCount();
}

function escapeHtml(str) {
  return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// ── Settings panel ─────────────────────────────────────────────────────────
function openSettings() {
  settingsPanel.classList.add('open');
  settingsOverlay.style.display = '';
}

function closeSettingsPanel() {
  settingsPanel.classList.remove('open');
  settingsOverlay.style.display = 'none';
  connectionResult.style.display = 'none';
}

function updateToggleUI(on) {
  toggleTrack.style.background = on ? 'rgba(168,85,247,.6)' : 'rgba(255,255,255,.1)';
  toggleThumb.style.left = on ? '22px' : '2px';
}

// ── Backend health ─────────────────────────────────────────────────────────
async function checkBackend() {
  try {
    const r = await fetch(`${state.apiUrl}/health`, { signal: AbortSignal.timeout(3000) });
    if (r.ok) {
      backendDot.style.background = '#7a9e6e';
      backendStatus.textContent = 'Connected';
      backendStatus.style.color = '#7a9e6e';
    } else throw new Error();
  } catch {
    backendDot.style.background = '#c97a6a';
    backendStatus.textContent = 'Offline';
    backendStatus.style.color = '#c97a6a';
  }
}

// ── Start ──────────────────────────────────────────────────────────────────
init();
