import asyncio
from collections import deque

from agent_loop import run_agent_loop
from events import AgentEndEvent, AgentStartEvent, MessageEvent
from providers.base import AssistantReply, ToolCall
from tools.agent_tool import AgentTool
from tools.helpers import write_to_file_tool


class FakeProvider:
    def __init__(self, replies: list[AssistantReply]) -> None:
        self.replies = replies
        self.calls = 0
        self.messages: list[list[dict]] = []

    async def complete(
        self, system: str, messages: list[dict], tools: list[dict]
    ) -> AssistantReply:
        self.messages.append(messages.copy())
        reply = self.replies[self.calls]
        self.calls += 1
        return reply


def echo(value: str) -> dict[str, object]:
    return {"ok": True, "value": value}


echo_tool = AgentTool(
    name="echo",
    description="Echo a value.",
    parameters={"value": {"type": "string"}},
    func=echo,
)


async def collect_events(
    provider: FakeProvider,
    tools: list[AgentTool],
    max_loop_iterations: int = 10,
    steering_messages: deque[str] | None = None,
) -> list[object]:
    queue = steering_messages if steering_messages is not None else deque()

    return [
        event
        async for event in run_agent_loop(
            provider=provider,
            tools=tools,
            messages=[],
            max_loop_iterations=max_loop_iterations,
            system="test",
            steering_messages=queue,
        )
    ]


def test_final_reply_ends_as_completed() -> None:
    async def scenario() -> None:
        provider = FakeProvider([AssistantReply(content="done")])
        events = await collect_events(provider, tools=[])

        assert isinstance(events[0], AgentStartEvent)
        assert events[-1] == AgentEndEvent(reason="completed")
        assert provider.calls == 1

    asyncio.run(scenario())


def test_tool_call_is_followed_by_another_provider_turn() -> None:
    async def scenario() -> None:
        provider = FakeProvider(
            [
                AssistantReply(
                    content=None,
                    tool_calls=[ToolCall("1", "echo", {"value": "x"})],
                ),
                AssistantReply(content="finished"),
            ]
        )
        events = await collect_events(provider, tools=[echo_tool])

        assert provider.calls == 2
        assert events[-1] == AgentEndEvent(reason="completed")

    asyncio.run(scenario())


def test_tool_loop_writes_file(tmp_path) -> None:
    async def scenario() -> None:
        target = tmp_path / "hello.txt"
        provider = FakeProvider(
            [
                AssistantReply(
                    content=None,
                    tool_calls=[
                        ToolCall(
                            "1",
                            "write_to_file",
                            {"filename": str(target), "content": "Hello, World!"},
                        )
                    ],
                ),
                AssistantReply(content="Done."),
            ]
        )
        events = await collect_events(provider, tools=[write_to_file_tool])

        assert target.read_text() == "Hello, World!"
        assert events[-1] == AgentEndEvent(reason="completed")

    asyncio.run(scenario())


def test_history_round_trip_order(tmp_path) -> None:
    async def scenario() -> None:
        target = tmp_path / "ignored.txt"
        provider = FakeProvider(
            [
                AssistantReply(
                    content=None,
                    tool_calls=[
                        ToolCall(
                            "1",
                            "write_to_file",
                            {"filename": str(target), "content": "ignored"},
                        )
                    ],
                ),
                AssistantReply(content="Done."),
            ]
        )
        messages: list[dict[str, object]] = [
            {"role": "user", "content": "write a file"}
        ]

        events = [
            event
            async for event in run_agent_loop(
                provider=provider,
                tools=[write_to_file_tool],
                messages=messages,
                max_loop_iterations=10,
                system="test",
                steering_messages=deque(),
            )
        ]

        assert len(provider.messages) == 2
        assert provider.messages[0] == [{"role": "user", "content": "write a file"}]
        second = provider.messages[1]
        assert [message["role"] for message in second] == [
            "user",
            "assistant",
            "tool",
        ]
        assert second[1]["tool_calls"][0]["function"]["name"] == "write_to_file"
        assert second[2]["tool_call_id"] == "1"
        assert events[-1] == AgentEndEvent(reason="completed")

    asyncio.run(scenario())


def test_max_iterations_is_reported_only_when_exhausted() -> None:
    async def scenario() -> None:
        provider = FakeProvider(
            [
                AssistantReply(
                    content=None,
                    tool_calls=[ToolCall("1", "echo", {"value": "x"})],
                )
            ]
        )
        events = await collect_events(
            provider, tools=[echo_tool], max_loop_iterations=1
        )

        assert events[-1] == AgentEndEvent(reason="max_iterations")
        assert isinstance(events[-2], MessageEvent)

    asyncio.run(scenario())


def test_final_reply_on_last_allowed_turn_is_completed() -> None:
    async def scenario() -> None:
        provider = FakeProvider([AssistantReply(content="done")])
        events = await collect_events(provider, tools=[], max_loop_iterations=1)

        assert events[-1] == AgentEndEvent(reason="completed")

    asyncio.run(scenario())


def test_pending_steering_after_final_reply_starts_next_turn() -> None:
    async def scenario() -> None:
        queue: deque[str] = deque()

        class SteeringProvider(FakeProvider):
            async def complete(
                self, system: str, messages: list[dict], tools: list[dict]
            ) -> AssistantReply:
                reply = await super().complete(system, messages, tools)
                if self.calls == 1:
                    queue.append("please revise")
                return reply

        provider = SteeringProvider(
            [AssistantReply(content="first"), AssistantReply(content="revised")]
        )
        events = await collect_events(provider, tools=[], steering_messages=queue)

        assert provider.calls == 2
        assert events[-1] == AgentEndEvent(reason="completed")

    asyncio.run(scenario())


def test_steering_messages_are_consumed_one_per_turn() -> None:
    async def scenario() -> None:
        queue: deque[str] = deque(["first steering", "second steering"])
        provider = FakeProvider(
            [AssistantReply(content="first"), AssistantReply(content="second")]
        )

        await collect_events(provider, tools=[], steering_messages=queue)

        assert provider.calls == 2
        assert provider.messages[0] == [{"role": "user", "content": "first steering"}]
        assert provider.messages[1] == [
            {"role": "user", "content": "first steering"},
            {"role": "assistant", "content": "first"},
            {"role": "user", "content": "second steering"},
        ]
        assert not queue

    asyncio.run(scenario())


def test_cancellation_emits_cancelled_end_event() -> None:
    async def scenario() -> None:
        started = asyncio.Event()

        class BlockingProvider:
            async def complete(
                self, system: str, messages: list[dict], tools: list[dict]
            ) -> AssistantReply:
                started.set()
                await asyncio.Event().wait()
                return AssistantReply(content="unreachable")

        events: list[object] = []

        async def consume() -> None:
            async for event in run_agent_loop(
                provider=BlockingProvider(),
                tools=[],
                messages=[],
                max_loop_iterations=2,
                system="test",
                steering_messages=deque(),
            ):
                events.append(event)

        task = asyncio.create_task(consume())
        await started.wait()
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass

        assert AgentEndEvent(reason="cancelled") in events

    asyncio.run(scenario())
