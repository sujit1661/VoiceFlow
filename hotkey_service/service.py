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
        self.record_thread  = None
        self.pa             = pyaudio.PyAudio()
        self.mic_stream     = None

        print("━" * 52)
        print("  Flow — Global Hotkey Service")
        print("  Built by Sujit Sadalage")
        print("━" * 52)
        print(f"  API      : {API_BASE}")
        print(f"  Context  : {CONTEXT}")
        print(f"  Overlay  : ws://127.0.0.1:{WS_PORT}")
        print()
        print("  Hold Ctrl  →  start recording")
        print("  Release    →  transcribe + polish + type")
        print("  ESC        →  quit")
        print("━" * 52)

    # ── Recording ─────────────────────────────────────────────────────────────
    def start_recording(self):
        self.recording    = True
        self.audio_frames = []
        broadcast("recording")
        print("  🔴 Recording…")
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

            # 2. Polish + real-time type via WebSocket stream ──────────────────
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
                broadcast("done", "Done ✨")

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
        Connect to backend WebSocket, receive tokens in real time,
        type each token as it arrives, broadcast preview to overlay.
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
                    # Type the token immediately (real-time)
                    _type_text(token)
                    # Broadcast last ~40 chars as preview
                    broadcast("token", full[-40:])

                elif t == "done":
                    full = pkt.get("full_text", full)
                    break

                elif t == "error":
                    print(f"  ❌ Stream error: {pkt.get('message')}")
                    break

            ws.close()
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
            if key == keyboard.Key.esc:
                print("\n  👋 Stopped.")
                return False
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
    """Type text via clipboard paste (unicode-safe) or pyautogui fallback."""
    if not text:
        return
    try:
        import pyperclip
        import pyautogui
        pyperclip.copy(text)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.02)   # small gap between tokens so paste doesn't merge
    except ImportError:
        try:
            import pyautogui
            pyautogui.typewrite(text, interval=0.018)
        except Exception as e:
            print(f"  ⚠️  Could not type: {e}")


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
