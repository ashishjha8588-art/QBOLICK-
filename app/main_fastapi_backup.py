"""Layer 6: FastAPI backend - sab kuch yahin judta hai."""
import base64
import hmac
import logging
import time
from collections import defaultdict, deque
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import brain
from .config import (APP_PASSWORD, ASSISTANT_NAME, MAX_AUDIO_MB, GROQ_API_KEY,
                     RATE_LIMIT_PER_MIN)
from .speech_to_text import transcribe
from .text_to_speech import speak

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("jarvis")

BASE_DIR = Path(__file__).resolve().parent.parent
app = FastAPI(title=f"{ASSISTANT_NAME} Voice Assistant")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

if not GROQ_API_KEY:
    log.warning("GROQ_API_KEY set nahi hai - AI features kaam nahi karenge.")
if not APP_PASSWORD:
    log.warning("APP_PASSWORD set nahi hai - app public hai, deploy se pehle password lagao!")

_hits: dict[str, deque] = defaultdict(deque)


def guard(request: Request, x_access_code: str = Header(default="")) -> None:
    """Password check + simple rate limit."""
    if APP_PASSWORD and not hmac.compare_digest(x_access_code.encode(), APP_PASSWORD.encode()):
        raise HTTPException(status_code=401, detail="Wrong or missing access code.")
    forwarded = request.headers.get("x-forwarded-for", "")
    ip = forwarded.split(",")[0].strip() or (request.client.host if request.client else "unknown")
    now = time.monotonic()
    hits = _hits[ip]
    while hits and now - hits[0] > 60:
        hits.popleft()
    if len(hits) >= RATE_LIMIT_PER_MIN:
        raise HTTPException(status_code=429, detail="Too many requests. Wait a minute.")
    hits.append(now)


def clean_session(value: str) -> str:
    return "".join(ch for ch in value if ch.isalnum() or ch in "-_")[:64] or "default"


def ai_error(exc: Exception) -> HTTPException:
    log.error("AI error: %s", type(exc).__name__)
    return HTTPException(502, "The AI service had a problem. Check server logs.")


async def make_reply(session_id: str, text: str) -> dict:
    try:
        reply, actions = await brain.think(session_id, text)
    except Exception as exc:
        raise ai_error(exc) from exc
    audio = await speak(reply)
    return {
        "reply": reply,
        "actions": actions,
        "audio_b64": base64.b64encode(audio).decode() if audio else None,
        "audio_mime": "audio/mpeg",
    }


class ChatIn(BaseModel):
    text: str
    session_id: str = "default"


@app.get("/")
async def home():
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.get("/health")
async def health():
    return {"status": f"{ASSISTANT_NAME} online"}


@app.get("/api/check", dependencies=[Depends(guard)])
async def check():
    return {"ok": True, "name": ASSISTANT_NAME}


@app.post("/api/chat", dependencies=[Depends(guard)])
async def chat(body: ChatIn):
    text = body.text.strip()[:2000]
    if not text:
        raise HTTPException(400, "Empty message.")
    return {"transcript": text, **await make_reply(clean_session(body.session_id), text)}


@app.post("/api/voice", dependencies=[Depends(guard)])
async def voice(audio: UploadFile = File(...), session_id: str = Form("default")):
    data = await audio.read()
    if len(data) > MAX_AUDIO_MB * 1024 * 1024:
        raise HTTPException(413, f"Audio too large (max {MAX_AUDIO_MB} MB).")
    if len(data) < 500:
        raise HTTPException(400, "Audio too short.")
    try:
        transcript = await transcribe(data, audio.content_type or "audio/webm")
    except Exception as exc:
        raise ai_error(exc) from exc
    if not transcript:
        return {"transcript": "", "reply": "", "actions": [], "audio_b64": None, "audio_mime": None}
    return {"transcript": transcript, **await make_reply(clean_session(session_id), transcript)}


@app.post("/api/reset", dependencies=[Depends(guard)])
async def reset(body: ChatIn):
    brain.reset(clean_session(body.session_id))
    return {"ok": True}
