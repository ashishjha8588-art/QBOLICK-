"""Layer 4: Tools / Actions.

Rule: model sirf request karta hai, asli kaam YAHAN ke Python functions karte hain.
Har tool chhota, safe aur validated hai. Khatarnak kaam (jaise door unlock) ke liye
server-side confirmation zaroori hai.
"""
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx

from .config import DEFAULT_CITY, DEFAULT_TIMEZONE

ROOMS = ["desk", "bedroom", "living room", "kitchen"]

# Demo state (memory me). Asli device ke liye niche "IoT" wale comments dekho.
light_state: dict[str, bool] = {room: False for room in ROOMS}
door_state: dict[str, str] = {"front door": "locked"}

# Unlock confirmation: session -> us turn ka number jab pehli baar unlock maanga gaya
_pending_unlock: dict[str, int] = {}

WEATHER_CODES = {
    0: "clear sky", 1: "mostly clear", 2: "partly cloudy", 3: "overcast",
    45: "foggy", 48: "foggy", 51: "light drizzle", 53: "drizzle", 55: "heavy drizzle",
    61: "light rain", 63: "rain", 65: "heavy rain", 71: "light snow", 73: "snow",
    75: "heavy snow", 80: "rain showers", 81: "rain showers", 82: "heavy rain showers",
    95: "thunderstorm", 96: "thunderstorm with hail", 99: "thunderstorm with hail",
}


def _tool(name: str, description: str, properties: dict, required: list[str]) -> dict:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {"type": "object", "properties": properties, "required": required},
        },
    }


TOOL_SCHEMAS = [
    _tool(
        "get_current_time",
        "Get the current date and time.",
        {"timezone": {"type": "string", "description": "IANA timezone, e.g. Asia/Kolkata. Optional."}},
        [],
    ),
    _tool(
        "get_weather",
        "Get the current weather for a city.",
        {"city": {"type": "string", "description": "City name. Optional, defaults to the user's home city."}},
        [],
    ),
    _tool(
        "set_timer",
        "Start a countdown timer for the user.",
        {
            "seconds": {"type": "integer", "description": "Timer length in seconds (1 to 86400)."},
            "label": {"type": "string", "description": "Short name for the timer, e.g. tea."},
        },
        ["seconds"],
    ),
    _tool(
        "control_light",
        "Turn a light on or off in a room.",
        {
            "room": {"type": "string", "enum": ROOMS},
            "state": {"type": "string", "enum": ["on", "off"]},
        },
        ["room", "state"],
    ),
    _tool(
        "set_door_lock",
        "Lock or unlock the front door. Unlocking needs the user's explicit confirmation.",
        {"state": {"type": "string", "enum": ["locked", "unlocked"]}},
        ["state"],
    ),
]


# ---------- tool functions ----------

async def get_current_time(ctx: dict, timezone: str = "") -> dict:
    try:
        tz = ZoneInfo(timezone or DEFAULT_TIMEZONE)
    except Exception:  # noqa: BLE001
        tz = ZoneInfo(DEFAULT_TIMEZONE)
    now = datetime.now(tz)
    return {"ok": True, "time": now.strftime("%I:%M %p"), "date": now.strftime("%A, %d %B %Y"), "timezone": str(tz)}


async def get_weather(ctx: dict, city: str = "") -> dict:
    city = (city or DEFAULT_CITY).strip()
    async with httpx.AsyncClient(timeout=8) as http:
        geo = await http.get(
            "https://geocoding-api.open-meteo.com/v1/search", params={"name": city, "count": 1}
        )
        results = geo.json().get("results")
        if not results:
            return {"ok": False, "error": f"City not found: {city}"}
        place = results[0]
        forecast = await http.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
                "timezone": "auto",
            },
        )
        cur = forecast.json()["current"]
    return {
        "ok": True,
        "city": place["name"],
        "temperature_c": cur["temperature_2m"],
        "humidity_percent": cur["relative_humidity_2m"],
        "wind_kmh": cur["wind_speed_10m"],
        "condition": WEATHER_CODES.get(cur["weather_code"], "unknown"),
    }


async def set_timer(ctx: dict, seconds: int, label: str = "") -> dict:
    seconds = int(seconds)
    if not 1 <= seconds <= 86400:
        return {"ok": False, "error": "Timer must be between 1 second and 24 hours."}
    label = (label or "Timer").strip()[:40]
    # Timer browser me chalta hai (tab khula rehna chahiye). "action" client ko bheja jata hai.
    return {"ok": True, "message": f"Timer '{label}' started for {seconds} seconds.",
            "action": {"type": "timer", "seconds": seconds, "label": label}}


async def control_light(ctx: dict, room: str, state: str) -> dict:
    room = room.lower().strip()
    if room not in ROOMS or state not in ("on", "off"):
        return {"ok": False, "error": f"Room must be one of: {', '.join(ROOMS)}."}
    light_state[room] = state == "on"
    # IoT: yahan asli device control lagao. Example (Home Assistant):
    #   await http.post(f"{HA_URL}/api/services/light/turn_{state}",
    #                   headers={"Authorization": f"Bearer {HA_TOKEN}"},
    #                   json={"entity_id": "light.desk"})
    return {"ok": True, "message": f"The {room} light is now {state}.",
            "action": {"type": "light", "room": room, "state": state}}


async def set_door_lock(ctx: dict, state: str) -> dict:
    if state not in ("locked", "unlocked"):
        return {"ok": False, "error": "State must be locked or unlocked."}
    session, turn = ctx["session_id"], ctx["turn"]
    if state == "unlocked":
        asked_at = _pending_unlock.get(session)
        # Confirmation tabhi maani jayegi jab user ne pehle request ke BAAD naya message bheja ho.
        if asked_at is None or asked_at >= turn:
            _pending_unlock[session] = turn
            return {"ok": False, "needs_confirmation": True,
                    "message": "Not unlocked yet. Ask the user to confirm they really want to unlock the door."}
        _pending_unlock.pop(session, None)
    door_state["front door"] = state
    return {"ok": True, "message": f"The front door is now {state}.",
            "action": {"type": "door", "state": state}}


_TOOLS = {
    "get_current_time": get_current_time,
    "get_weather": get_weather,
    "set_timer": set_timer,
    "control_light": control_light,
    "set_door_lock": set_door_lock,
}


async def run_tool(name: str, args: dict, ctx: dict) -> dict:
    func = _TOOLS.get(name)
    if func is None:
        return {"ok": False, "error": f"Unknown tool: {name}"}
    try:
        return await func(ctx, **args)
    except TypeError:
        return {"ok": False, "error": "Bad arguments for this tool."}
    except Exception:  # noqa: BLE001
        return {"ok": False, "error": f"{name} failed. Try again later."}
