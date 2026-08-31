import asyncio
import json

from providers.base import Provider
from tools import tool_map, tools

max_loop_iterations = 10  # Set a maximum number of iterations to prevent infinite loops
system = """
You are a helpful coding assistant. You help users by reading files, executing commands, editing code, and writing new files.
"""


async def run_agent_loop(provider: Provider, messages: list[dict] | None = None):
    if messages is None:
        messages = []

    for _ in range(max_loop_iterations):
        response = await provider.complete(
            system=system, messages=messages, tools=tools
        )
        if not response:
            print("No response from provider.")
            break

        print(f"=== Assistant: {response.content}")
        if not response.tool_calls:
            print(response.content)
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
                result = tool(**tool_args)
                print(
                    f"Tool {tool_name} called with arguments {tool_args}. Result: {result}"
                )
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_id,
                        "content": json.dumps(result, ensure_ascii=False),
                    }
                )
            else:
                print(f"Tool {tool_name} not found.")
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


if __name__ == "__main__":
    import asyncio

    from providers.deepseek import DeepSeekProvider

    provider = DeepSeekProvider()

    asyncio.run(
        run_agent_loop(
            provider=provider,
            messages=[
                {
                    "role": "user",
                    "content": "创建一个 test.txt文件，内容为 'Hello, World!'",
                }
            ],
        )
    )
