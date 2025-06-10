import mimetypes
import re
from collections.abc import AsyncGenerator

from acp_sdk import Message
from acp_sdk.models import MessagePart
from acp_sdk.server import Context, Server
from beeai_framework.backend import AssistantMessage, SystemMessage, UserMessage
from beeai_framework.backend.chat import ChatModel

CODE_BLOCK_REGEX = re.compile(r"[\n^]```(?P<type>\w+)\s+(?P<name>\S+)\s*\n(?P<content>.*?)\n```", re.DOTALL)

SYSTEM_PROMPT = """You are a helpful assistant. Based on the user's request, generate the required content.

In your message, use markdown with named markdown code blocks.

Re-use the same name when the user asks for modifications to the previous content.

For more complex cases, like programming, you may use subfolders in the names.

For example, if the user asks for a poem, you may output:

> Here's a poem about AI:
>
> ```text ode_to_ai.txt
> <poem content>
> ```

And if the user asks for a hello world project in Python, you may output:

> Here's a hello world project in Python:
>
> ```python hello_world.py
> print("Hello, world!")
> ```
>
> ```toml pyproject.toml
> [project]
> name = "hello-world"
> version = "0.1.0"
> description = "A simple hello world project"
> ```
"""

server = Server()


@server.agent()
async def canvas_agent(input: list[Message], context: Context) -> AsyncGenerator:
    """
    An agent that processes user input and generates named artifacts based on the request.
    It instructs the LLM to create named markdown code blocks like:
    ```text document.txt
    ... content ...
    ```
    These blocks are then parsed and returned as named MessageParts.
    """

    llm = ChatModel.from_name("ollama:gemma3:12b-it-qat")

    response = await llm.create(messages=[
        SystemMessage(SYSTEM_PROMPT),
        *(
            (UserMessage if message.role == "user" else AssistantMessage)(str(message))
            for message in input
        ),
    ])
    response_text = response.get_text_content()

    last_end = 0
    for match in CODE_BLOCK_REGEX.finditer(response_text):
        if text_part := response_text[last_end : match.start()].strip():
            yield MessagePart(content=text_part, content_type="text/plain")

        yield MessagePart(
            content=match.group("content").strip(),
            name=(name := match.group("name")),
            content_type=mimetypes.guess_type(name)[0] or "text/plain",
        )
        last_end = match.end()

    if text_part := response_text[last_end:].strip():
        yield MessagePart(content=text_part, content_type="text/plain")


if __name__ == "__main__":
    server.run()
