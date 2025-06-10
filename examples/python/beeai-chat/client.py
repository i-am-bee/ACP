import asyncio
import sys
from contextlib import suppress

from acp_sdk import GenericEvent, MessageCompletedEvent, MessagePartEvent
from acp_sdk.client import Client
from acp_sdk.models import Message, MessagePart


async def run_client() -> None:
    with suppress(EOFError):
        async with Client(base_url="http://localhost:8000") as client, client.session() as session:
            while True:
                user_message = input(">>> ")
                user_message_input = Message(parts=[MessagePart(content=user_message)])

                log_type = None
                async for event in client.run_stream(agent="chat_agent", input=[user_message_input]):
                    match event:
                        case MessagePartEvent(part=MessagePart(content=content)):
                            if log_type:
                                print()
                                log_type = None
                            print(content, end="", flush=True)
                        case GenericEvent():
                            [(new_log_type, content)] = event.generic.model_dump().items()
                            if new_log_type != log_type:
                                if log_type is not None:
                                    print()
                                print(f"{new_log_type}: ", end="", file=sys.stderr, flush=True)
                                log_type = new_log_type
                            print(content, end="", file=sys.stderr, flush=True)
                        case MessageCompletedEvent():
                            print()
                        case _:
                            if log_type:
                                print()
                                log_type = None
                            print(f"ℹ️ {event.type}", file=sys.stderr)


if __name__ == "__main__":
    asyncio.run(run_client())
