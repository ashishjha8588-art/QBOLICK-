"""Layer 5: Text -> deep server voice using Groq Orpheus."""
import logging
import httpx

from .config import GROQ_API_KEY, TTS_MODEL, TTS_VOICE

log = logging.getLogger("jarvis.tts")


async def speak(text: str) -> bytes | None:
    """Groq Orpheus se WAV audio bytes return karta hai."""
    if not text.strip() or not GROQ_API_KEY:
        return None

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    data = {
        "model": TTS_MODEL,
        "voice": TTS_VOICE,
        "input": "[gravelly authoritative] " + text.strip()[:170],
        "response_format": "wav",
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as http:
            response = await http.post(
                "https://api.groq.com/openai/v1/audio/speech",
                headers=headers,
                json=data,
            )
            print("TTS ERROR BODY:", response.text); response.raise_for_status()
            return response.content
    except Exception:
        log.exception("TTS failed, browser voice use hogi")
        return None
