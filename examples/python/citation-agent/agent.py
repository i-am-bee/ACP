from collections.abc import AsyncGenerator

from acp_sdk import Message, Metadata
from acp_sdk.models import MessagePart
from acp_sdk.server import Context, Server

server = Server()


@server.agent(metadata=Metadata(ui={"type": "hands-off", "user_greeting": "What topic do you want to research?"}))
async def citation_agent(input: list[Message], context: Context) -> AsyncGenerator:
    yield MessagePart(
        content="This is a testing citation",
        metadata={"kind": "citation", "data": {"url": "https://www.ibm.com", "start_index": 9, "end_index": 25}},
    )


server.run()
