"""
Flow — Voice to Text API
Built by Sujit Sadalage
Production-ready FastAPI backend for deployment.
"""

import os
import json
import tempfile
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, Form, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from groq import Groq
from dotenv import load_dotenv

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("flow")

# ── Load env ──────────────────────────────────────────────────────────────────
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
ENVIRONMENT  = os.getenv("ENVIRONMENT", "development")   # "production" | "development"
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:8000,http://localhost:3000,http://127.0.0.1:8000"
).split(",")

# In production allow *, set ALLOWED_ORIGINS env var instead of hardcoding
if ENVIRONMENT == "production":
    ALLOWED_ORIGINS = ["*"]

# ── Groq client (lazy init so missing key doesn't crash startup) ───────────────
_groq_client: Groq | None = None

def get_client() -> Groq:
    global _groq_client
    if _groq_client is None:
        if not GROQ_API_KEY:
            raise RuntimeError("GROQ_API_KEY is not set. Add it to your .env or environment variables.")
        _groq_client = Groq(api_key=GROQ_API_KEY)
    return _groq_client

# ── App factory ───────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Flow API starting — environment: %s", ENVIRONMENT)
    yield
    log.info("Flow API shutting down.")

app = FastAPI(
    title="Flow Voice API",
    description="Voice-to-text + AI polishing API. Built by Sujit Sadalage.",
    version="1.0.0",
    lifespan=lifespan,
    # Hide docs in production (optional — remove if you want Swagger UI)
    docs_url=None if ENVIRONMENT == "production" else "/docs",
    redoc_url=None if ENVIRONMENT == "production" else "/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# ── Frontend directory — resolve relative to this file ────────────────────────
# Works whether you run from backend/ or the project root
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))          # .../backend/
FRONTEND_DIR = os.path.normpath(os.path.join(BASE_DIR, "..", "frontend"))  # .../frontend/

log.info("Frontend directory: %s (exists=%s)", FRONTEND_DIR, os.path.isdir(FRONTEND_DIR))

# ── Mount CSS/JS static assets ────────────────────────────────────────────────
# We mount /css and /js separately so API routes (/api/*, /ws/*) still work.
_css_dir = os.path.join(FRONTEND_DIR, "css")
_js_dir  = os.path.join(FRONTEND_DIR, "js")
if os.path.isdir(_css_dir):
    app.mount("/css", StaticFiles(directory=_css_dir), name="css")
if os.path.isdir(_js_dir):
    app.mount("/js",  StaticFiles(directory=_js_dir),  name="js")

# ── Context prompts ───────────────────────────────────────────────────────────
CONTEXT_PROMPTS = {
    "email":    "You are an expert email writer. Polish this dictated text into a professional, well-formatted email. Fix grammar, punctuation, and structure. Remove filler words. Keep the original meaning.",
    "document": "You are a professional writer. Polish this dictated text into a clean, well-formatted paragraph. Fix grammar, punctuation, and formatting. Remove filler words. Keep the original meaning.",
    "note":     "Polish this dictated text into clean, concise notes. Fix grammar and punctuation. Remove filler words. Keep the original meaning.",
    "chat":     "Polish this dictated text into a natural, casual message. Fix obvious errors but keep the conversational tone. Remove filler words.",
    "code":     "This is a code-related dictation. Polish the technical description, fix grammar and punctuation. Keep technical terms exact.",
    "general":  "Polish this dictated text. Fix grammar, punctuation, and formatting. Remove filler words (um, uh, like, you know). Keep the original meaning intact.",
}

# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/", include_in_schema=False)
async def root():
    """Serve the landing page."""
    idx = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.isfile(idx):
        return FileResponse(idx, media_type="text/html")
    return {"name": "Flow Voice API", "version": "1.0.0", "status": "ok"}

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "environment": ENVIRONMENT, "groq_configured": bool(GROQ_API_KEY)}

@app.post("/api/transcribe")
async def transcribe_audio(audio: UploadFile = File(...)):
    """Transcribe audio using Groq Whisper Large v3."""
    tmp_path = None
    try:
        audio_bytes = await audio.read()
        if len(audio_bytes) < 500:
            return JSONResponse({"success": False, "error": "Audio too short", "text": ""}, 400)

        suffix = ".webm" if "webm" in (audio.content_type or "") else ".wav"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        client = get_client()
        with open(tmp_path, "rb") as f:
            transcription = client.audio.transcriptions.create(
                model="whisper-large-v3",
                file=(audio.filename or f"audio{suffix}", f, audio.content_type or "audio/webm"),
                response_format="text",
            )

        text = transcription.strip() if isinstance(transcription, str) else str(transcription).strip()
        log.info("Transcribed %d chars", len(text))
        return {"success": True, "text": text, "raw": text}

    except RuntimeError as e:
        log.error("Config error: %s", e)
        return JSONResponse({"success": False, "error": str(e), "text": ""}, 500)
    except Exception as e:
        log.error("Transcription error: %s", e)
        return JSONResponse({"success": False, "error": str(e), "text": ""}, 500)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

@app.post("/api/polish")
async def polish_text(
    text: str = Form(...),
    context: str = Form(default="general"),
):
    """Polish transcribed text using Groq LLaMA 3.1."""
    if not text.strip():
        return JSONResponse({"success": False, "error": "No text provided", "polished": ""}, 400)
    try:
        prompt = CONTEXT_PROMPTS.get(context, CONTEXT_PROMPTS["general"])
        client = get_client()
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Polish this text:\n\n{text}\n\nReturn ONLY the polished text, no explanations."},
            ],
            temperature=0.3,
            max_tokens=2048,
        )
        polished = completion.choices[0].message.content.strip()
        log.info("Polished %d→%d chars [%s]", len(text), len(polished), context)
        return {"success": True, "polished": polished, "original": text}
    except RuntimeError as e:
        return JSONResponse({"success": False, "error": str(e), "polished": text}, 500)
    except Exception as e:
        log.error("Polish error: %s", e)
        return JSONResponse({"success": False, "error": str(e), "polished": text}, 500)

@app.websocket("/ws/stream")
async def websocket_stream(websocket: WebSocket):
    """WebSocket endpoint — streams polished text token-by-token."""
    await websocket.accept()
    try:
        while True:
            raw = await websocket.receive_text()
            payload = json.loads(raw)
            text    = payload.get("text", "").strip()
            context = payload.get("context", "general")

            if not text:
                await websocket.send_text(json.dumps({"type": "error", "message": "No text provided"}))
                continue

            prompt = CONTEXT_PROMPTS.get(context, CONTEXT_PROMPTS["general"])
            client = get_client()
            stream = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"Polish this text:\n\n{text}\n\nReturn ONLY the polished text, no explanations."},
                ],
                temperature=0.3,
                max_tokens=2048,
                stream=True,
            )

            await websocket.send_text(json.dumps({"type": "start"}))
            full = ""
            for chunk in stream:
                token = chunk.choices[0].delta.content
                if token:
                    full += token
                    await websocket.send_text(json.dumps({"type": "token", "token": token}))
            await websocket.send_text(json.dumps({"type": "done", "full_text": full}))

    except WebSocketDisconnect:
        log.info("WebSocket client disconnected")
    except RuntimeError as e:
        try: await websocket.send_text(json.dumps({"type": "error", "message": str(e)}))
        except: pass
    except Exception as e:
        log.error("WebSocket error: %s", e)
        try: await websocket.send_text(json.dumps({"type": "error", "message": "Server error"}))
        except: pass

# ── Catch-all: serve HTML pages ───────────────────────────────────────────────
@app.get("/{page_path:path}", include_in_schema=False)
async def serve_page(page_path: str):
    """Serve any frontend HTML file by name, e.g. /app.html, /features.html"""
    # Security: only allow simple filenames, no path traversal
    safe = os.path.basename(page_path)
    file_path = os.path.join(FRONTEND_DIR, safe)
    if os.path.isfile(file_path):
        # Determine media type
        if safe.endswith(".html"):
            return FileResponse(file_path, media_type="text/html")
        return FileResponse(file_path)
    # Fall back to index for SPA routing
    idx = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.isfile(idx):
        return FileResponse(idx, media_type="text/html")
    return JSONResponse({"error": "Not found"}, status_code=404)
