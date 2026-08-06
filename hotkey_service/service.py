"""
Flow — Global Hotkey Service
Built by Sujit Sadalage

Hold Ctrl → records mic → transcribes → AI polishes → real-time auto-types.
Overlay is handled by Electron (no browser tab, no tkinter).
Broadcasts state via WebSocket on port 8765.
"""

import threading
import asyncio
import time
import tempfile
import wave
import json
import os
import sys
import requests
import pyaudio
from pynput import keyboard

try:
    import websockets
    import websockets.server
except ImportError:
    print("  ❌  websockets not installed. Run:  pip install websockets")
    sys.exit(1)

# ── Config ────────────────────────────────────────────────────────────────────
API_BASE    = os.getenv("FLOW_API",     "http://localhost:8000")
WS_API_BASE = API_BASE.replace("http://", "ws://").replace("https://", "wss://")
CONTEXT     = os.getenv("FLOW_CONTEXT", "general")
WS_PORT     = 8765          # overlay WebSocket port

# Set FLOW_AUTO_POLISH=false to type the raw transcript without AI polishing
AUTO_POLISH = os.getenv("FLOW_AUTO_POLISH", "true").lower() not in ("false", "0", "no")

CHUNK    = 1024
FORMAT   = pyaudio.paInt16
CHANNELS = 1
RATE     = 16000

# ═══════════════════════════════════════════════════════════════════════════════
#  WEBSOCKET BROADCAST SERVER  (service → Electron overlay)
# ═══════════════════════════════════════════════════════════════════════════════
_clients:  set = set()
_ws_loop: asyncio.AbstractEventLoop | None = None


async def _ws_handler(ws):
    _clients.add(ws)
    try:
        async for _ in ws:
            pass
    except Exception:
        pass
    finally:
        _clients.discard(ws)


async def _run_server():
    async with websockets.server.serve(_ws_handler, "127.0.0.1", WS_PORT):
        await asyncio.get_event_loop().create_future()   # run forever


def _start_ws_server():
    global _ws_loop
    _ws_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_ws_loop)
    _ws_loop.run_until_complete(_run_server())


def broadcast(state: str, text: str = ""):
    """Thread-safe broadcast to all connected Electron overlay clients."""
    if not _ws_loop or not _clients:
        return
    msg = json.dumps({"state": state, "text": text})

    async def _send():
        dead = set()
        for ws in list(_clients):
            try:
                await ws.send(msg)
            except Exception:
                dead.add(ws)
        _clients.difference_update(dead)

    asyncio.run_coroutine_threadsafe(_send(), _ws_loop)


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN SERVICE
# ═══════════════════════════════════════════════════════════════════════════════
class FlowService:

    def __init__(self):
        self.recording      = False
        self.audio_frames   = []
        self.ctrl_pressed   = False
        self.cancelled      = False      # True when ESC is pressed mid-recording
        self.record_thread  = None
        self.pa             = pyaudio.PyAudio()
        self.mic_stream     = None
        self._shift_pressed = False

        print("━" * 52)
        print("  Flow — Global Hotkey Service")
        print("  Built by Sujit Sadalage")
        print("━" * 52)
        print(f"  API        : {API_BASE}")
        print(f"  Context    : {CONTEXT}")
        print(f"  Auto-Polish: {'ON' if AUTO_POLISH else 'OFF (typing raw transcript)'}")
        print(f"  Overlay    : ws://127.0.0.1:{WS_PORT}")
        print()
        print("  Hold Ctrl  →  start recording")
        print("  Release    →  transcribe + polish + type")
        print("  ESC        →  cancel current recording")
        print("  Shift+ESC  →  quit service")
        print("━" * 52)

    # ── Audio feedback ────────────────────────────────────────────────────────
    @staticmethod
    def _beep(frequency: int = 880, duration_ms: int = 80, volume: float = 0.25):
        """Play a short beep using PyAudio (non-blocking via thread)."""
        def _play():
            try:
                import math
                pa = pyaudio.PyAudio()
                rate = 44100
                samples = int(rate * duration_ms / 1000)
                stream = pa.open(format=pyaudio.paFloat32, channels=1, rate=rate, output=True)
                # Simple sine wave with a short fade-out to avoid click
                buf = bytes()
                for i in range(samples):
                    fade = 1.0 - (i / samples) ** 0.5   # sqrt fade
                    val = volume * fade * math.sin(2 * math.pi * frequency * i / rate)
                    buf += __import__('struct').pack('<f', val)
                stream.write(buf)
                stream.stop_stream()
                stream.close()
                pa.terminate()
            except Exception:
                pass   # beep is best-effort; never crash the service
        threading.Thread(target=_play, daemon=True).start()

    # ── Recording ─────────────────────────────────────────────────────────────
    def start_recording(self):
        self.recording    = True
        self.cancelled    = False
        self.audio_frames = []
        broadcast("recording")
        print("  🔴 Recording…")
        self._beep(frequency=880, duration_ms=80)   # high beep = start
        try:
            self.mic_stream = self.pa.open(
                format=FORMAT, channels=CHANNELS,
                rate=RATE, input=True, frames_per_buffer=CHUNK
            )
            while self.recording:
                data = self.mic_stream.read(CHUNK, exception_on_overflow=False)
                self.audio_frames.append(data)
        except Exception as e:
            print(f"  ❌ Mic error: {e}")
        finally:
            if self.mic_stream:
                self.mic_stream.stop_stream()
                self.mic_stream.close()
                self.mic_stream = None

    def stop_and_process(self):
        self.recording = False
        if self.record_thread:
            self.record_thread.join(timeout=2)

        if self.cancelled:
            broadcast("cancelled", "Recording discarded")
            print("  ✋ Recording cancelled")
            self._beep(frequency=300, duration_ms=120)  # low double beep = cancel
            time.sleep(0.12)
            self._beep(frequency=300, duration_ms=120)
            return

        self._beep(frequency=660, duration_ms=80)   # mid beep = stop/processing

        if not self.audio_frames:
            broadcast("no_speech", "No audio captured")
            print("  ⚠️  No audio captured")
            return

        # Save WAV
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp_path = tmp.name
        with wave.open(tmp_path, "wb") as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(self.pa.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b"".join(self.audio_frames))

        try:
            # 1. Transcribe ────────────────────────────────────────────────────
            broadcast("processing", "Transcribing with Whisper…")
            print("  ⏳ Transcribing…")
            with open(tmp_path, "rb") as f:
                resp = requests.post(
                    f"{API_BASE}/api/transcribe",
                    files={"audio": ("audio.wav", f, "audio/wav")},
                    timeout=30,
                )
            data     = resp.json()
            raw_text = data.get("text", "").strip()

            if not raw_text:
                broadcast("no_speech", "No speech detected")
                print("  ⚠️  No speech detected")
                return

            print(f"  📝 {raw_text[:70]}{'…' if len(raw_text) > 70 else ''}")

            # 2. Polish or type raw depending on AUTO_POLISH setting ───────────
            if AUTO_POLISH:
                broadcast("polishing", "AI polishing…")
                print("  ✨ Polishing + typing in real time…")
                # Small delay so cursor stays in the target window after Ctrl release
                time.sleep(0.35)
                full_text = self._stream_polish_and_type(raw_text)
                if full_text:
                    broadcast("done", "Done ✨")
                    print(f"  ✅ Typed: {full_text[:60]}{'…' if len(full_text) > 60 else ''}")
                else:
                    _type_text(raw_text)
                    broadcast("done", "Done (raw)")
            else:
                broadcast("typing", raw_text[:50])
                print("  ⌨️  Typing raw transcript…")
                time.sleep(0.35)
                _type_text(raw_text)
                broadcast("done", "Done")
                print(f"  ✅ Typed (raw): {raw_text[:60]}{'…' if len(raw_text) > 60 else ''}")

        except requests.exceptions.ConnectionError:
            msg = f"Cannot connect to {API_BASE}"
            broadcast("error", msg)
            print(f"  ❌ {msg}")
        except Exception as e:
            broadcast("error", str(e)[:50])
            print(f"  ❌ {e}")
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

    def _stream_polish_and_type(self, raw_text: str) -> str:
        """
        Connect to backend WebSocket, receive tokens in real time.
        Broadcasts a live preview to the overlay as tokens arrive,
        then types the complete polished text in ONE paste at the end
        (avoids clipboard-race from per-token pasting).
        Returns the full polished text (empty string on failure).
        """
        ws_url = f"{WS_API_BASE}/ws/stream"
        full   = ""

        try:
            import websocket   # websocket-client (sync)
        except ImportError:
            print("  ℹ️  websocket-client not installed, falling back to REST polish")
            return self._rest_polish_and_type(raw_text)

        try:
            ws = websocket.create_connection(ws_url, timeout=30)
            ws.send(json.dumps({"text": raw_text, "context": CONTEXT}))

            broadcast("typing", "")

            while True:
                msg = ws.recv()
                pkt = json.loads(msg)
                t   = pkt.get("type")

                if t == "start":
                    continue

                elif t == "token":
                    token = pkt.get("token", "")
                    full += token
                    # Broadcast last ~40 chars as overlay preview ONLY — don't type yet
                    broadcast("token", full[-40:])

                elif t == "done":
                    full = pkt.get("full_text", full).strip()
                    break

                elif t == "error":
                    print(f"  ❌ Stream error: {pkt.get('message')}")
                    break

            ws.close()

            # Type the complete polished text in one shot (no clipboard race)
            if full:
                _type_text(full)

            return full

        except Exception as e:
            print(f"  ⚠️  WebSocket stream failed ({e}), falling back to REST")
            return self._rest_polish_and_type(raw_text)

    def _rest_polish_and_type(self, raw_text: str) -> str:
        """Fallback: REST polish then type all at once."""
        broadcast("polishing", "AI cleaning your text…")
        pr = requests.post(
            f"{API_BASE}/api/polish",
            data={"text": raw_text, "context": CONTEXT},
            timeout=30,
        )
        polished = pr.json().get("polished", raw_text).strip()
        broadcast("typing", polished[:50])
        _type_text(polished)
        return polished

    # ── Keyboard handlers ─────────────────────────────────────────────────────
    def on_press(self, key):
        try:
            if key in (keyboard.Key.ctrl_r, keyboard.Key.ctrl_l):
                if not self.ctrl_pressed:
                    self.ctrl_pressed = True
                    threading.Timer(0.4, self._try_start).start()
            elif key == keyboard.Key.esc:
                if self.recording:
                    # ESC mid-recording: cancel (discard audio, don't type anything)
                    print("  ✋ ESC pressed — cancelling recording")
                    self.cancelled = True
                    self.recording = False
                    threading.Thread(
                        target=self.stop_and_process, daemon=True
                    ).start()
                elif self._shift_pressed:
                    # Shift+ESC when idle: quit the service
                    print("\n  👋 Shift+ESC — Stopped.")
                    return False
            elif key in (keyboard.Key.shift, keyboard.Key.shift_r, keyboard.Key.shift_l):
                self._shift_pressed = True
        except Exception:
            pass

    def _try_start(self):
        if self.ctrl_pressed and not self.recording:
            self.record_thread = threading.Thread(
                target=self.start_recording, daemon=True
            )
            self.record_thread.start()

    def on_release(self, key):
        try:
            if key in (keyboard.Key.shift, keyboard.Key.shift_r, keyboard.Key.shift_l):
                self._shift_pressed = False
            if key in (keyboard.Key.ctrl_r, keyboard.Key.ctrl_l):
                self.ctrl_pressed = False
                if self.recording:
                    threading.Thread(
                        target=self.stop_and_process, daemon=True
                    ).start()
        except Exception:
            pass

    def run(self):
        with keyboard.Listener(
            on_press=self.on_press, on_release=self.on_release
        ) as listener:
            listener.join()
        self.pa.terminate()


# ── Auto-type helper ──────────────────────────────────────────────────────────
def _type_text(text: str):
    """
    Type text via clipboard paste (unicode-safe, handles any character).
    Saves and restores the clipboard so user doesn't lose what they had copied.
    Falls back to pyautogui.typewrite for ASCII-only text if pyperclip is absent.
    """
    if not text:
        return
    try:
        import pyperclip
        import pyautogui

        # Save previous clipboard contents so we can restore after paste
        try:
            previous = pyperclip.paste()
        except Exception:
            previous = ""

        pyperclip.copy(text)
        time.sleep(0.05)          # let clipboard settle before pasting
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.12)          # wait for paste to land in target window

        # Restore previous clipboard after a short delay
        def _restore():
            time.sleep(0.4)
            try:
                pyperclip.copy(previous)
            except Exception:
                pass
        threading.Thread(target=_restore, daemon=True).start()

    except ImportError:
        try:
            import pyautogui
            # typewrite only works reliably with ASCII; warn for non-ASCII
            safe = text.encode("ascii", errors="replace").decode("ascii")
            pyautogui.typewrite(safe, interval=0.018)
        except Exception as e:
            print(f"  ⚠️  Could not type text: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    # 1. Start WebSocket broadcast server in background
    ws_thread = threading.Thread(target=_start_ws_server, daemon=True)
    ws_thread.start()
    time.sleep(0.3)   # let server bind

    print("  🖥️  Waiting for Electron overlay to connect…")
    print("  ▶   Run:  cd electron && npm start")
    print()

    # 2. Run hotkey listener on main thread (blocking)
    svc = FlowService()
    svc.run()
