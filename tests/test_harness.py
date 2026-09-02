import asyncio

import pytest

from events import AgentEndEvent
from harness import AgentHarness
from providers.base import AssistantReply


class ImmediateProvider:
    async def complete(
        self, system: str, messages: list[dict], tools: list[dict]
    ) -> AssistantReply:
        return AssistantReply(content="done")


class BlockingProvider:
    def __init__(self) -> None:
        self.started = asyncio.Event()
        self.release = asyncio.Event()

    async def complete(
        self, system: str, messages: list[dict], tools: list[dict]
    ) -> AssistantReply:
        self.started.set()
        await self.release.wait()
        return AssistantReply(content="done")


def test_prompt_returns_async_iterator_and_cleans_up() -> None:
    async def scenario() -> None:
        harness = AgentHarness(provider=ImmediateProvider(), tools=[])
        iterator = harness.prompt("hello")

        assert hasattr(iterator, "__aiter__")
        assert harness.is_running is True

        events = [event async for event in iterator]

        assert events[-1] == AgentEndEvent(reason="completed")
        assert harness.is_running is False

    asyncio.run(scenario())


def test_prompt_rejects_concurrent_run_and_cancel_cleans_up() -> None:
    async def scenario() -> None:
        provider = BlockingProvider()
        harness = AgentHarness(provider=provider, tools=[])

        async def consume() -> list[object]:
            return [event async for event in harness.prompt("hello")]

        task = asyncio.create_task(consume())
        await provider.started.wait()

        with pytest.raises(RuntimeError):
            harness.prompt("second")

        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

        assert harness.is_running is False

    asyncio.run(scenario())


def test_steer_requires_active_run() -> None:
    async def scenario() -> None:
        harness = AgentHarness(provider=ImmediateProvider(), tools=[])

        with pytest.raises(RuntimeError):
            harness.steer("not running")

    asyncio.run(scenario())
