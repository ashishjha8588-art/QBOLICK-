import asyncio
from app.brain import think

async def main():
    reply, actions = await think("test", "Hello Jarvis")
    print("REPLY:", reply)
    print("ACTIONS:", actions)

asyncio.run(main())
