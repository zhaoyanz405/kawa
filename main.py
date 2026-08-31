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


async def run_agent_loop(
    provider: Provider,
    tools: list[dict],
    messages: list[dict] | None = None,
):
    if messages is None:
        messages = []

    yield AgentStartEvent()

    for _ in range(max_loop_iterations):
        response = await provider.complete(
            system=system,
            messages=messages,
            tools=tools,
        )

        yield MessageEvent(role="assistant", content=response.content)
        if not response.tool_calls:
            break

        messages.append(
            {
                "role": "assistant",
                "content": response.content,
                "tool_calls": [
                    {
                        "id": call.id,
                        "type": "function",
                        "function": {
                            "name": call.name,
                            "arguments": json.dumps(call.arguments, ensure_ascii=False),
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
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_id,
                        "content": json.dumps(result, ensure_ascii=False),
                    }
                )
            else:
                yield ToolExecutionStartEvent(name=tool_name, arguments=tool_args)
                yield ToolExecutionEndEvent(name=tool_name, result={"error": f"Tool {tool_name} not found."})
                messages.append(
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

async def main():
    from providers.deepseek import DeepSeekProvider

    provider = DeepSeekProvider()

    async for event in run_agent_loop(
        provider=provider,
        messages=[
            {
                "role": "user",
                "content": "创建一个 test.txt文件，内容为 'Hello, World!'",
            }
        ],
        tools=[tool.input_schema() for tool in tool_map.values()]
    ):
        print(event)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
