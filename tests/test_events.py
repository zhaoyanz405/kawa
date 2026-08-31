import asyncio

from fake_provider import FakeProvider

from events import (
    AgentEndEvent,
    AgentStartEvent,
    MessageEvent,
    ToolExecutionEndEvent,
)
from main import run_agent_loop
from providers.base import AssistantReply, ToolCall
from tools.helpers import write_to_file_tool


async def collect(*args, **kwargs):
    return [event async for event in run_agent_loop(*args, **kwargs)]


def test_direct_answer_event_sequence():
    provider = FakeProvider([AssistantReply(content="Hi!", tool_calls=[])])

    events = asyncio.run(
        collect(
            provider,
            tools=[write_to_file_tool.input_schema()],
            messages=[{"role": "user", "content": "hi"}],
        )
    )

    assert [type(e).__name__ for e in events] == [
        "AgentStartEvent",
        "MessageEvent",
        "AgentEndEvent",
    ]


def test_tool_loop_event_sequence(tmp_path):
    target = tmp_path / "hello.txt"
    provider = FakeProvider(
        [
            AssistantReply(
                content=None,
                tool_calls=[
                    ToolCall(
                        id="call-1",
                        name="write_to_file",
                        arguments={"filename": str(target), "content": "Hello!"},
                    )
                ],
            ),
            AssistantReply(content="Done.", tool_calls=[]),
        ]
    )

    events = asyncio.run(
        collect(
            provider,
            tools=[write_to_file_tool.input_schema()],
            messages=[{"role": "user", "content": "write a file"}],
        )
    )

    assert [type(e).__name__ for e in events] == [
        "AgentStartEvent",
        "MessageEvent",
        "ToolExecutionStartEvent",
        "ToolExecutionEndEvent",
        "MessageEvent",
        "AgentEndEvent",
    ]
    assert isinstance(events[0], AgentStartEvent)
    assert isinstance(events[-1], AgentEndEvent)
    assert isinstance(events[3], ToolExecutionEndEvent)
    assert events[3].name == "write_to_file"
    assert events[3].result == {"ok": True, "filename": str(target)}


def test_event_sequence_is_consumable_by_any_consumer():
    provider = FakeProvider([AssistantReply(content="Hi!", tool_calls=[])])

    rendered: list[str] = []

    async def render():
        async for event in run_agent_loop(
            provider,
            tools=[write_to_file_tool.input_schema()],
            messages=[{"role": "user", "content": "hi"}],
        ):
            if isinstance(event, MessageEvent):
                rendered.append(f"[{event.role}] {event.content}")

    asyncio.run(render())

    assert rendered == ["[assistant] Hi!"]
