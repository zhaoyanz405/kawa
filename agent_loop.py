import asyncio
import json
from collections import deque
from collections.abc import AsyncIterator

from events import (
    AgentEndEvent,
    AgentEvent,
    AgentStartEvent,
    EndReason,
    MessageEvent,
    ToolExecutionEndEvent,
    ToolExecutionStartEvent,
)
from providers.base import Provider
from tools.agent_tool import AgentTool


async def run_agent_loop(
    provider: Provider,
    tools: list[AgentTool],
    messages: list[dict[str, object]],
    max_loop_iterations: int,
    system: str,
    steering_messages: deque[str],
) -> AsyncIterator[AgentEvent]:
    if max_loop_iterations < 1:
        raise ValueError("max_loop_iterations must be at least 1")

    yield AgentStartEvent()

    tool_map = {tool.name: tool for tool in tools}
    turns_used = 0
    end_reason: EndReason | None = None

    try:
        while turns_used < max_loop_iterations:
            if steering_messages:
                messages.append(
                    {"role": "user", "content": steering_messages.popleft()}
                )

            turns_used += 1
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

                if not steering_messages:
                    end_reason = "completed"
                    break

                continue

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
                else:
                    result = {"error": f"Tool {tool_name} not found."}
                    yield ToolExecutionStartEvent(name=tool_name, arguments=tool_args)

                yield ToolExecutionEndEvent(name=tool_name, result=result)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_id,
                        "content": json.dumps(result, ensure_ascii=False),
                    }
                )

        if end_reason is None:
            yield MessageEvent(
                role="assistant",
                content="Maximum loop iterations reached. Stopping the agent.",
            )
            end_reason = "max_iterations"

        yield AgentEndEvent(reason=end_reason)
    except asyncio.CancelledError:
        yield AgentEndEvent(reason="cancelled")
        raise
