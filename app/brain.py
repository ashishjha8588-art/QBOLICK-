"""Layer 3: LLM (dimaag) + tool calling loop + chhoti memory."""
import json

from .client import client
from .config import LLM_MODEL, MAX_HISTORY, SYSTEM_PROMPT
from .tools import TOOL_SCHEMAS, run_tool

_history: dict[str, list[dict]] = {}   # session_id -> [{"role", "content"}, ...]
_turns: dict[str, int] = {}            # session_id -> kitne user messages aaye


def reset(session_id: str) -> None:
    _history.pop(session_id, None)
    _turns.pop(session_id, None)


async def think(session_id: str, user_text: str) -> tuple[str, list[dict]]:
    """User ka text lo -> (jawab, client ko bhejne wale actions)."""
    history = _history.setdefault(session_id, [])
    _turns[session_id] = _turns.get(session_id, 0) + 1
    history.append({"role": "user", "content": user_text})

    ctx = {"session_id": session_id, "turn": _turns[session_id]}
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history
    actions: list[dict] = []
    reply = ""

    for _ in range(5):  # tool calls ka loop (infinite na chale)
        response = await client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            tools=TOOL_SCHEMAS,
            tool_choice="auto",
        )
        msg = response.choices[0].message

        if not msg.tool_calls:
            reply = (msg.content or "").strip()
            break

        messages.append({
            "role": "assistant",
            "content": msg.content,
            "tool_calls": [
                {"id": c.id, "type": "function",
                 "function": {"name": c.function.name, "arguments": c.function.arguments}}
                for c in msg.tool_calls
            ],
        })
        for call in msg.tool_calls:
            try:
                args = json.loads(call.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            result = await run_tool(call.function.name, args, ctx)
            action = result.pop("action", None)
            if action:
                actions.append(action)
            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": json.dumps(result, ensure_ascii=False),
            })

    if not reply:
        reply = "Sorry, I could not finish that. Please try again."

    history.append({"role": "assistant", "content": reply})
    del history[:-MAX_HISTORY]
    return reply, actions
