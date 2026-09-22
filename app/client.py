import httpx

from .config import GROQ_API_KEY


class Function:
    def __init__(self, data):
        self.name = data["function"]["name"]
        self.arguments = data["function"].get("arguments", "{}")


class ToolCall:
    def __init__(self, data):
        self.id = data["id"]
        self.type = data.get("type", "function")
        self.function = Function(data)


class Message:
    def __init__(self, data):
        self.content = data.get("content")
        self.tool_calls = [
            ToolCall(x) for x in (data.get("tool_calls") or [])
        ]


class Choice:
    def __init__(self, data):
        self.message = Message(data["message"])


class Response:
    def __init__(self, data):
        self.choices = [Choice(x) for x in data["choices"]]


class ChatCompletions:
    async def create(self, **kwargs):
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=60.0) as http:
            response = await http.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=kwargs,
            )
            response.raise_for_status()
            return Response(response.json())


class Client:
    def __init__(self):
        self.chat = type(
            "Chat",
            (),
            {"completions": ChatCompletions()}
        )()


client = Client()
