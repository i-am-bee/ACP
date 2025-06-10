from collections.abc import AsyncGenerator

import beeai_framework
from acp_sdk import Message
from acp_sdk.models import MessagePart
from acp_sdk.server import Context, Server
from beeai_framework.agents.react import ReActAgent, ReActAgentUpdateEvent
from beeai_framework.backend import AssistantMessage, UserMessage
from beeai_framework.backend.chat import ChatModel, ChatModelParameters
from beeai_framework.memory import TokenMemory
from beeai_framework.tools.search.duckduckgo import DuckDuckGoSearchTool
from beeai_framework.tools.search.wikipedia import WikipediaTool
from beeai_framework.tools.tool import AnyTool
from beeai_framework.tools.weather.openmeteo import OpenMeteoTool

server = Server()


def to_framework_message(role: str, content: str) -> beeai_framework.backend.Message:
    match role:
        case "user":
            return UserMessage(content)
        case "agent":
            return AssistantMessage(content)
        case _:
            raise ValueError(f"Unsupported role {role}")


@server.agent()
async def chat_agent(input: list[Message], context: Context) -> AsyncGenerator:
    """
    The agent is an AI-powered conversational system with memory, supporting real-time search, Wikipedia lookups,
    and weather updates through integrated tools.
    """

    # ensure the model is pulled before running
    llm = ChatModel.from_name(
        "ollama:llama3.1", ChatModelParameters(temperature=0))

    # Configure tools
    tools: list[AnyTool] = [WikipediaTool(), OpenMeteoTool(),
                            DuckDuckGoSearchTool()]

    # Create agent with memory and tools
    agent = ReActAgent(llm=llm, tools=tools, memory=TokenMemory(llm))

    history = [message async for message in context.session.load_history()]
    framework_messages = [
        to_framework_message(message.role, str(message)) for message in history + input
    ]
    await agent.memory.add_many(framework_messages)

    async for data, event in agent.run():
        match (data, event.name):
            case (ReActAgentUpdateEvent(), "partial_update"):
                update = data.update.value
                if not isinstance(update, str):
                    update = update.get_text_content()
                match data.update.key:
                    case "thought" | "tool_name" | "tool_input" | "tool_output":
                        yield {data.update.key: update}
                    case "final_answer":
                        yield Message(role="agent", parts=[MessagePart(content=update)])
                last_key = data.update.key


if __name__ == "__main__":
    server.run()
