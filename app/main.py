"""Layer 6: Starlette backend - Mini-Jarvis."""
import base64
import hmac
import json
import logging
import time
from collections import defaultdict, deque
from pathlib import Path

from starlette.applications import Starlette
from starlette.datastructures import UploadFile
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from . import brain
from .config import (
    APP_PASSWORD,
    ASSISTANT_NAME,
    GROQ_API_KEY,
    MAX_AUDIO_MB,
    RATE_LIMIT_PER_MIN,
)
from .speech_to_text import transcribe
from .text_to_speech import speak

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("jarvis")

BASE_DIR = Path(__file__).resolve().parent.parent

if not GROQ_API_KEY:
    log.warning("GROQ_API_KEY set nahi hai - AI features kaam nahi karenge.")
if not APP_PASSWORD:
    log.warning("APP_PASSWORD set nahi hai - app public hai, deploy se pehle password lagao!")

_hits: dict[str, deque] = defaultdict(deque)


def guard(request: Request) -> None:
    x_access_code = request.headers.get("x-access-code", "")

    if APP_PASSWORD and not hmac.compare_digest(
        x_access_code.encode(), APP_PASSWORD.encode()
    ):
        raise HTTPException(status_code=401, detail="Wrong or missing access code.")

    forwarded = request.headers.get("x-forwarded-for", "")
    ip = forwarded.split(",")[0].strip() or (
        request.client.host if request.client else "unknown"
    )

    now = time.monotonic()
    hits = _hits[ip]

    while hits and now - hits[0] > 60:
        hits.popleft()

    if len(hits) >= RATE_LIMIT_PER_MIN:
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Wait a minute.",
        )

    hits.append(now)


def clean_session(value: str) -> str:
    return "".join(ch for ch in value if ch.isalnum() or ch in "-_")[:64] or "default"


def ai_error(exc: Exception) -> HTTPException:
    log.error("AI error: %s", type(exc).__name__)
    return HTTPException(
        status_code=502,
        detail="The AI service had a problem. Check server logs.",
    )


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
        "audio_mime": "audio/wav",
    }


async def home(request: Request):
    return FileResponse(BASE_DIR / "static" / "index.html")


async def health(request: Request):
    return JSONResponse({"status": f"{ASSISTANT_NAME} online"})


async def check(request: Request):
    guard(request)
    return JSONResponse({"ok": True, "name": ASSISTANT_NAME})


async def chat(request: Request):
    guard(request)

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON.")

    text = str(body.get("text", "")).strip()[:2000]
    session_id = str(body.get("session_id", "default"))

    if not text:
        raise HTTPException(status_code=400, detail="Empty message.")

    result = await make_reply(clean_session(session_id), text)

    return JSONResponse({"transcript": text, **result})


async def voice(request: Request):
    guard(request)

    form = await request.form()
    upload = form.get("audio")
    session_id = str(form.get("session_id", "default"))

    if not isinstance(upload, UploadFile):
        raise HTTPException(status_code=400, detail="Audio file missing.")

    data = await upload.read()

    if len(data) > MAX_AUDIO_MB * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"Audio too large (max {MAX_AUDIO_MB} MB).",
        )

    if len(data) < 500:
        raise HTTPException(status_code=400, detail="Audio too short.")

    try:
        transcript = await transcribe(
            data,
            upload.content_type or "audio/webm",
        )
    except Exception as exc:
        raise ai_error(exc) from exc

    if not transcript:
        return JSONResponse(
            {
                "transcript": "",
                "reply": "",
                "actions": [],
                "audio_b64": None,
                "audio_mime": None,
            }
        )

    result = await make_reply(clean_session(session_id), transcript)

    return JSONResponse({"transcript": transcript, **result})


async def reset(request: Request):
    guard(request)

    try:
        body = await request.json()
    except Exception:
        body = {}

    session_id = str(body.get("session_id", "default"))
    brain.reset(clean_session(session_id))

    return JSONResponse({"ok": True})


routes = [
    Route("/", home, methods=["GET"]),
    Route("/health", health, methods=["GET"]),
    Route("/api/check", check, methods=["GET"]),
    Route("/api/chat", chat, methods=["POST"]),
    Route("/api/voice", voice, methods=["POST"]),
    Route("/api/reset", reset, methods=["POST"]),
    Mount(
        "/static",
        app=StaticFiles(directory=BASE_DIR / "static"),
        name="static",
    ),
]

app = Starlette(
    debug=False,
    routes=routes,
)
