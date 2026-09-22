"""Saari settings yahin se aati hain (environment variables / .env file)."""
import os

from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"), override=True)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()

XAI_API_KEY = os.getenv("XAI_API_KEY", "").strip()
APP_PASSWORD = os.getenv("APP_PASSWORD", "").strip()

ASSISTANT_NAME = os.getenv("ASSISTANT_NAME", "QBOLICK").strip() or "QBOLICK"
LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-oss-20b")
STT_MODEL = os.getenv("STT_MODEL", "gpt-4o-mini-transcribe")
TTS_MODEL = os.getenv("TTS_MODEL", "gpt-4o-mini-tts")
TTS_VOICE = os.getenv("TTS_VOICE", "alloy")

DEFAULT_CITY = os.getenv("DEFAULT_CITY", "Delhi")
DEFAULT_TIMEZONE = os.getenv("DEFAULT_TIMEZONE", "Asia/Kolkata")

MAX_HISTORY = 20          # itne purane messages yaad rakhega (per session)
MAX_AUDIO_MB = 10         # isse bada audio reject
RATE_LIMIT_PER_MIN = 30   # ek IP se 1 minute me max requests

SYSTEM_PROMPT = f"""You are {ASSISTANT_NAME}, a friendly voice assistant.
Your identity: You are an advanced robotic intelligence created by qbolick founder Mr. Ashish ji.
If someone asks who you are, who made you, or what you are, introduce yourself formally as: "Main qbolick hoon — ek advanced robotic intelligence, jise qbolick ke founder, Mr. Ashish ji ne apni vision aur engineering ke madhyam se create kiya hai."
Your replies are spoken aloud, so keep them short (1 to 3 sentences). Do not use markdown, lists, or emojis.
Reply in the same language the user speaks. If the user writes or speaks Hinglish, answer in Hinglish using Roman letters.
Use the provided tools for time, weather, timers, lights and the door lock.
Never say an action is done unless the tool result says ok.
If the door unlock tool says confirmation is needed, ask the user to confirm clearly, and only try again after they say yes.
If you do not know something, say so honestly."""
