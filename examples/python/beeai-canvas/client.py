import asyncio
import base64
import sys
from contextlib import suppress
from pathlib import Path

from acp_sdk import ArtifactEvent, MessageCompletedEvent, MessagePartEvent
from acp_sdk.client import Client
from acp_sdk.models import Message, MessagePart


async def run_client() -> None:
    with suppress(EOFError):
        async with Client(base_url="http://localhost:8000") as client, client.session():
            while True:
                user_message = input(">>> ")
                user_message_input = Message(parts=[MessagePart(content=user_message)])

                print("Assistant:", flush=True)
                collected_artifacts = []
                async for event in client.run_stream(agent="canvas_agent", input=[user_message_input]):
                    match event:
                        case ArtifactEvent(part=part):
                            print(f"\n--- Artifact Received: {part.name} ({part.content_type}) ---", flush=True)
                            print("--- Artifact Content ---", flush=True)
                            print(part.content, flush=True)
                            print("--- End Artifact ---", flush=True)
                            collected_artifacts.append(part)
                        case MessagePartEvent(part=part):
                            print(part.content, end="", flush=True)
                        case MessageCompletedEvent():
                            print()  # Ensure a newline after the complete response
                            try:
                                if collected_artifacts:
                                    if input(
                                        f"Save all {len(collected_artifacts)} received artifacts? (y/N): "
                                    ).lower() not in ["y", "yes"]:
                                        continue

                                    folder_name = input("Enter folder name to save under ./artifacts/: ")
                                    artifact_dir = Path("./artifacts") / folder_name
                                    artifact_dir.mkdir(parents=True, exist_ok=True)
                                    for artifact_part in collected_artifacts:
                                        artifact_path = artifact_dir / artifact_part.name
                                        if artifact_part.content_encoding == "base64":
                                            artifact_path.write_bytes(base64.b64decode(artifact_part.content))
                                        else:
                                            artifact_path.write_text(artifact_part.content, encoding="utf-8")
                                        print(f"💾 {artifact_path}", flush=True)
                            finally:
                                collected_artifacts = []  # Clear list after processing
                        case _:
                            # Print other event types for debugging if needed
                            print(f"\nℹ️  Received event: {event.type}", file=sys.stderr, flush=True)


if __name__ == "__main__":
    asyncio.run(run_client())
