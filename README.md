# Flow — Voice-to-Text AI

> **Don't type, just speak.** Flow turns natural speech into clear, polished writing — in every app, instantly.

Built by **Sujit Sadalage** · Powered by [Groq](https://groq.com) (Whisper Large v3 + LLaMA 3.1)

---

## What is Flow?

Flow is a voice dictation app that:
- **Records** your voice with a single hotkey (hold `Ctrl`)
- **Transcribes** speech using Groq's Whisper Large v3 (sub-second)
- **Polishes** the output using LLaMA 3.1 8B — removing filler words, fixing grammar, formatting for context
- **Types** the result wherever your cursor is (any app, globally)

Works in Gmail, Slack, VS Code, Notion, Word — anywhere.

---

## Project Structure

```
flow/
├── backend/
│   ├── main.py              # FastAPI server (transcribe + polish + WebSocket)
│   ├── requirements.txt     # Python dependencies
│   └── .env.example         # Environment variable template
├── frontend/
│   ├── index.html           # Landing page
│   ├── app.html             # Voice recording app
│   ├── features.html        # Features page
│   ├── use-cases.html       # Use cases page
│   ├── about.html           # About / Sujit Sadalage
│   ├── contact.html         # Contact form
│   ├── css/style.css        # App styles
│   └── js/app.js            # App JavaScript
├── hotkey_service/
│   ├── service.py           # Global hotkey + auto-type (Windows/Mac/Linux)
│   └── requirements.txt     # pynput, pyautogui, pyaudio
├── Procfile                 # For cloud deployment (FastAPI Cloud, Railway, Render)
├── start.bat                # Windows one-click launcher
└── README.md
```

---

## Quick Start (Local)

### 1. Get a free Groq API key

Sign up at [console.groq.com](https://console.groq.com) — it's free. Copy your key (starts with `gsk_...`).

### 2. Configure environment

```bash
cd backend
cp .env.example .env
# Edit .env and set your key:
# GROQ_API_KEY=gsk_your_key_here
```

### 3. Install and run

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Then open [http://localhost:8000](http://localhost:8000) in your browser.

**Windows shortcut:** double-click `start.bat` — it does everything automatically.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/api/transcribe` | Transcribe audio (multipart/form-data) |
| `POST` | `/api/polish` | Polish text with AI |
| `WS` | `/ws/stream` | Stream polished tokens in real-time |
| `GET` | `/*` | Serves frontend pages |

### POST `/api/transcribe`

```
audio  (file)    — Audio blob (.webm, .wav, .mp3)
```

```json
{ "success": true, "text": "Transcribed text here", "raw": "Transcribed text here" }
```

### POST `/api/polish`

```
text     (string)  — Raw transcript
context  (string)  — general | email | document | note | chat | code
```

```json
{ "success": true, "polished": "Clean polished text.", "original": "um like the raw text" }
```

### WebSocket `/ws/stream`

Send: `{ "text": "raw transcript", "context": "email" }`

Receive sequence:
```json
{ "type": "start" }
{ "type": "token", "token": "Hello" }
{ "type": "done", "full_text": "Hello, I wanted to reach out..." }
```

---

## Context Modes

| Mode | Best for |
|------|----------|
| `general` | Any dictation, catch-all |
| `email` | Professional email composition |
| `document` | Reports, articles, long-form writing |
| `note` | Quick notes, bullet points |
| `chat` | Slack, Teams, casual messages |
| `code` | Code comments, PR descriptions, docs |

---

## Global Hotkey Service (Types anywhere)

The hotkey service runs in the background and lets you dictate into **any application** — not just the browser.

```bash
cd hotkey_service
pip install -r requirements.txt
python service.py
```

| Action | What happens |
|--------|-------------|
| Hold **Ctrl** (0.5s) | Recording starts 🔴 |
| Release **Ctrl** | Transcribes → polishes → auto-types result ✨ |
| Press **ESC** | Quit the service |

> **Note for macOS:** You may need to grant Accessibility permission to Terminal in System Preferences → Security & Privacy → Accessibility.

> **Note for Linux:** Install portaudio first: `sudo apt install portaudio19-dev`

---

## Deploying to FastAPI Cloud / Railway / Render

The app is production-ready. The backend serves the frontend as static files.

### Environment variables to set in your cloud dashboard:

| Variable | Value |
|----------|-------|
| `GROQ_API_KEY` | Your Groq API key (`gsk_...`) |
| `ENVIRONMENT` | `production` |
| `ALLOWED_ORIGINS` | Your deployed domain, e.g. `https://flow.yourdomain.com` |

### Deploy command:

```bash
cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
```

The `Procfile` at the project root handles this automatically for Heroku-style platforms.

### What gets served:

- `/` → `frontend/index.html` (landing page)
- `/app.html` → Voice recording app
- `/features.html`, `/about.html`, `/contact.html`, etc. → All frontend pages
- `/api/*` → FastAPI endpoints
- `/ws/stream` → WebSocket

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python · FastAPI · Uvicorn |
| Transcription | Groq Whisper Large v3 (free tier) |
| AI Polishing | Groq LLaMA 3.1 8B Instant (free tier) |
| Frontend | HTML · CSS · Vanilla JavaScript · Tailwind CDN |
| Global Hotkey | pynput · pyaudio · pyautogui |
| Deployment | FastAPI Cloud · Railway · Render · Heroku |

---

## Troubleshooting

**"Cannot reach backend"**
→ Make sure `uvicorn main:app --reload` is running in the `backend/` folder.

**"Transcription failed" / API error**
→ Check your `GROQ_API_KEY` in `backend/.env`. Get a free key at [console.groq.com](https://console.groq.com).

**"No speech detected"**
→ Speak louder, hold the key longer, or check microphone permissions in the browser.

**PyAudio install fails on Windows**
→ Try: `pip install pipwin && pipwin install pyaudio`

**PyAudio install fails on Linux**
→ `sudo apt install portaudio19-dev python3-pyaudio`

---

## License

MIT — free to use, modify, and distribute.

---

## Built by

**Sujit Sadalage**
- GitHub: [github.com/sujitsadalage](https://github.com/sujitsadalage)
- LinkedIn: [linkedin.com/in/sujitsadalage](https://linkedin.com/in/sujitsadalage)
- Email: sujitsadalage@gmail.com

---

*Flow · © 2025 Sujit Sadalage · All rights reserved*
