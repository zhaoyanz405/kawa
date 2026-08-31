import asyncio

from fake_provider import FakeProvider

from events import MessageEvent
from main import run_agent_loop
from providers.base import AssistantReply, ToolCall
from tools.helpers import write_to_file_tool


async def collect(*args, **kwargs):
    return [event async for event in run_agent_loop(*args, **kwargs)]


def test_direct_answer_emits_assistant_message():
    provider = FakeProvider([AssistantReply(content="Hi there!", tool_calls=[])])
    messages = [{"role": "user", "content": "say hi"}]

    events = asyncio.run(
        collect(provider, tools=[write_to_file_tool.input_schema()], messages=messages)
    )

    assert provider.calls == [messages]
    texts = [e.content for e in events if isinstance(e, MessageEvent)]
    assert texts == ["Hi there!"]


def test_tool_loop_writes_file(tmp_path):
    target = tmp_path / "hello.txt"
    provider = FakeProvider(
        [
            AssistantReply(
                content=None,
                tool_calls=[
                    ToolCall(
                        id="call-1",
                        name="write_to_file",
                        arguments={"filename": str(target), "content": "Hello, World!"},
                    )
                ],
            ),
            AssistantReply(content="Done.", tool_calls=[]),
        ]
    )
    messages = [{"role": "user", "content": "write a file"}]

    asyncio.run(
        collect(provider, tools=[write_to_file_tool.input_schema()], messages=messages)
    )

    assert target.read_text() == "Hello, World!"


def test_history_round_trip_order(tmp_path):
    target = tmp_path / "ignored.txt"
    provider = FakeProvider(
        [
            AssistantReply(
                content=None,
                tool_calls=[
                    ToolCall(
                        id="call-1",
                        name="write_to_file",
                        arguments={"filename": str(target), "content": "ignored"},
                    )
                ],
            ),
            AssistantReply(content="Done.", tool_calls=[]),
        ]
    )
    messages = [{"role": "user", "content": "write a file"}]

    asyncio.run(
        collect(provider, tools=[write_to_file_tool.input_schema()], messages=messages)
    )

    assert len(provider.calls) == 2
    assert provider.calls[0] == [{"role": "user", "content": "write a file"}]
    second = provider.calls[1]
    assert [m["role"] for m in second] == ["user", "assistant", "tool"]
    assert second[1]["tool_calls"][0]["function"]["name"] == "write_to_file"
    assert second[2]["tool_call_id"] == "call-1"
