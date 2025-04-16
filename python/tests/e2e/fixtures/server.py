import base64
import time
from collections.abc import AsyncGenerator, AsyncIterator, Generator
from threading import Thread

import pytest
from acp_sdk.models import Artifact, Await, AwaitResume, Message, MessagePart
from acp_sdk.server import Context, Server

from e2e.config import Config


@pytest.fixture(scope="module")
def server() -> Generator[None]:
    server = Server()

    @server.agent()
    async def echo(inputs: list[Message], context: Context) -> AsyncIterator[Message]:
        for message in inputs:
            yield message

    @server.agent()
    async def awaiter(inputs: list[Message], context: Context) -> AsyncGenerator[Message | Await, AwaitResume]:
        yield Await()
        yield Message(MessagePart(content="empty", content_type="text/plain"))

    @server.agent()
    async def failer(inputs: list[Message], context: Context) -> AsyncIterator[Message]:
        raise RuntimeError("Whoops")

    @server.agent()
    async def sessioner(inputs: list[Message], context: Context) -> AsyncIterator[Message]:
        assert context.session_id is not None

        yield Message(MessagePart(content=str(context.session_id), content_type="text/plain"))

    @server.agent()
    async def mime_types(inputs: list[Message], context: Context) -> AsyncIterator[Message]:
        yield Message(
            MessagePart(content="<h1>HTML Content</h1>", content_type="text/html"),
            MessagePart(content='{"key": "value"}', content_type="application/json"),
            MessagePart(content="console.log('Hello');", content_type="application/javascript"),
            MessagePart(content="body { color: red; }", content_type="text/css"),
        )

    @server.agent()
    async def base64_encoding(inputs: list[Message], context: Context) -> AsyncIterator[Message]:
        yield Message(
            MessagePart(
                content=base64.b64encode(
                    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
                ).decode("ascii"),
                content_type="image/png",
                content_encoding="base64",
            ),
            MessagePart(content="This is plain text", content_type="text/plain"),
        )

    @server.agent()
    async def artifact_producer(inputs: list[Message], context: Context) -> AsyncGenerator[Message | Artifact, None]:
        yield Message(MessagePart(content="Processing with artifacts", content_type="text/plain"))
        yield Artifact(name="text-result.txt", content_type="text/plain", content="This is a text artifact result")
        yield Artifact(
            name="data.json", content_type="application/json", content='{"results": [1, 2, 3], "status": "complete"}'
        )
        yield Artifact(
            name="image.png",
            content_type="image/png",
            content=base64.b64encode(
                b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
            ).decode("ascii"),
            content_encoding="base64",
        )

    thread = Thread(target=server.run, kwargs={"port": Config.PORT}, daemon=True)
    thread.start()

    time.sleep(1)

    yield server

    server.should_exit = True
    thread.join(timeout=2)
