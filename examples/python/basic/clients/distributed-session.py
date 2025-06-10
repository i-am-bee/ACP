import asyncio

from acp_sdk.client import Client
from acp_sdk.models import MessagePart

# Assume setup with two independent servers (no shared infrastructure)
# For simplicity, both servers contain the same chat_agent. See examples/python/beeai-chat/agent.py

server_one = "http://localhost:8000"
server_two = "http://localhost:8001"

agent = "chat_agent"


async def example() -> None:
    async with Client() as client, client.session() as session_client:
        run = await session_client.run_sync(
            MessagePart(
                content="Hi, my name is Jon.",
            ),
            agent=agent,
            base_url=server_one,
        )  # server one
        run.raise_for_status()

        run = await session_client.run_sync(
            MessagePart(
                content="What is my name again?",
            ),
            agent=agent,
            base_url=server_two,
        )  # server two
        run.raise_for_status()

        print(run.output[0])  # Responds something like "Your name is Jon."


if __name__ == "__main__":
    asyncio.run(example())
