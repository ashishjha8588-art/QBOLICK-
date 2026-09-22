"""Layer 2: Awaaz (audio) -> text using Groq."""
import httpx

from .config import GROQ_API_KEY, STT_MODEL

_EXT = {
    "audio/webm": "webm",
    "audio/ogg": "ogg",
    "audio/mp4": "mp4",
    "audio/x-m4a": "m4a",
    "audio/mpeg": "mp3",
    "audio/wav": "wav",
    "audio/x-wav": "wav",
}


async def transcribe(audio_bytes: bytes, content_type: str = "audio/webm") -> str:
    base_type = (content_type or "audio/webm").split(";")[0].strip().lower()
    ext = _EXT.get(base_type, "webm")

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
    }

    files = {
        "file": (f"speech.{ext}", audio_bytes, base_type),
    }

    data = {
        "model": STT_MODEL,
        "response_format": "json",
    }

    async with httpx.AsyncClient(timeout=60.0) as http:
        response = await http.post(
            "https://api.groq.com/openai/v1/audio/transcriptions",
            headers=headers,
            files=files,
            data=data,
        )
        response.raise_for_status()
        result = response.json()

    return (result.get("text") or "").strip()
