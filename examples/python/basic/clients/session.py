import asyncio
from functools import reduce

from acp_sdk.client import Client
from acp_sdk.models import (
    Message,
    MessagePart,
)


async def example() -> None:
    async with Client(base_url="http://localhost:8000") as client, client.session() as session:
        run = await session.run_sync(
            agent="chat_agent",
            input=[
                Message(
                    parts=[
                        MessagePart(
                            content="Hi, my name is Jon. I like apples. Can you tell me something about them?",
                        )
                    ]
                )
            ],
        )
        print(str(reduce(lambda x, y: x + y, run.output)))
        run = await session.run_sync(
            agent="chat_agent",
            input=[Message(parts=[MessagePart(content="What is my favourite fruit?")])]
        )
        print(str(reduce(lambda x, y: x + y, run.output)))
        run = await session.run_sync(
            agent="chat_agent",
            input=[Message(parts=[MessagePart(content="Update the revious answer with my name.")])],
        )
        print(str(reduce(lambda x, y: x + y, run.output)))


if __name__ == "__main__":
    asyncio.run(example())
