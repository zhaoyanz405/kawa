import asyncio

from fake_provider import FakeProvider

from main import run_agent_loop
from providers.base import AssistantReply, ToolCall


def test_direct_answer_prints_and_stops(capsys):
    provider = FakeProvider([AssistantReply(content="Hi there!", tool_calls=[])])
    messages = [{"role": "user", "content": "say hi"}]

    asyncio.run(run_agent_loop(provider, messages))

    assert provider.calls == [messages]
    out = capsys.readouterr().out
    assert "Hi there!" in out


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

    asyncio.run(run_agent_loop(provider, messages))

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

    asyncio.run(run_agent_loop(provider, messages))

    assert len(provider.calls) == 2
    assert provider.calls[0] == [{"role": "user", "content": "write a file"}]
    second = provider.calls[1]
    assert [m["role"] for m in second] == ["user", "assistant", "tool"]
    assert second[1]["tool_calls"][0]["function"]["name"] == "write_to_file"
    assert second[2]["tool_call_id"] == "call-1"
