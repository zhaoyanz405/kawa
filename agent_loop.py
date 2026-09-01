import json
from events import (
    AgentEndEvent,
    AgentStartEvent,
    MessageEvent,
    ToolExecutionEndEvent,
    ToolExecutionStartEvent,
)


async def run_agent_loop(provider, tools, messages, max_loop_iterations, system):
    yield AgentStartEvent()

    tool_map = {tool.name: tool for tool in tools}

    for idx in range(max_loop_iterations):
        response = await provider.complete(
            system=system,
            messages=messages,
            tools=[tool.input_schema() for tool in tools],
        )

        yield MessageEvent(role="assistant", content=response.content)
        if not response.tool_calls:
            messages.append(
                {
                    "role": "assistant",
                    "content": response.content,
                }
            )
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
                yield ToolExecutionEndEvent(
                    name=tool_name, result={"error": f"Tool {tool_name} not found."}
                )
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

    if idx >= max_loop_iterations:
        yield MessageEvent(
            role="assistant",
            content="Maximum loop iterations reached. Stopping the agent.",
        )

    yield AgentEndEvent()
