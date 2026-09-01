import asyncio
import json

from events import (
    AgentEndEvent,
    AgentStartEvent,
    MessageEvent,
    ToolExecutionEndEvent,
    ToolExecutionStartEvent,
)
from providers.base import Provider
from tools import tool_map

max_loop_iterations = 10  # Set a maximum number of iterations to prevent infinite loops
system = """
You are a helpful coding assistant. You help users by reading files, executing commands, editing code, and writing new files.
"""


class AgentLoop:
    def __init__(
        self, provider: Provider, tools: list[dict], messages: list[dict] | None = None
    ):
        self.provider = provider
        self.tools = tools
        self._messages = messages if messages is not None else []

    def prompt(self, content: str):
        self._messages.append({"role": "user", "content": content})
        return self.run()

    async def _run_agent_loop(self):
        yield AgentStartEvent()

        for _ in range(max_loop_iterations):
            response = await self.provider.complete(
                system=system,
                messages=self._messages,
                tools=self.tools,
            )

            yield MessageEvent(role="assistant", content=response.content)
            if not response.tool_calls:
                break

            self._messages.append(
                {
                    "role": "assistant",
                    "content": response.content,
                    "tool_calls": [
                        {
                            "id": call.id,
                            "type": "function",
                            "function": {
                                "name": call.name,
                                "arguments": json.dumps(
                                    call.arguments, ensure_ascii=False
                                ),
                            },
                        }
                        for call in response.tool_calls
                    ],
                }
            )

            for call in response.tool_calls:
                tool_id = call.id
                tool_name = call.name
                tool_args = call.arguments

                tool = tool_map.get(tool_name)

                if tool:
                    yield ToolExecutionStartEvent(name=tool_name, arguments=tool_args)
                    result = tool.execute(tool_args)
                    yield ToolExecutionEndEvent(name=tool_name, result=result)
                    self._messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_id,
                            "content": json.dumps(result, ensure_ascii=False),
                        }
                    )
                else:
                    yield ToolExecutionStartEvent(name=tool_name, arguments=tool_args)
                    yield ToolExecutionEndEvent(
                        name=tool_name, result={"error": f"Tool {tool_name} not found."}
                    )
                    self._messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_id,
                            "content": json.dumps(
                                {"error": f"Tool {tool_name} not found."},
                                ensure_ascii=False,
                            ),
                        }
                    )

        yield AgentEndEvent()

    async def run(self):
        async for event in self._run_agent_loop():
            print(event)


if __name__ == "__main__":
    from providers.deepseek import DeepSeekProvider

    provider = DeepSeekProvider()

    loop = AgentLoop(
        provider=provider, tools=[tool.input_schema() for tool in tool_map.values()]
    )
    asyncio.run(
        loop.prompt("Write a file named hello.txt with the content 'Hello, World!'")
    )
