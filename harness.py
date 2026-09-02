from collections import deque
from collections.abc import AsyncIterator

from agent_loop import run_agent_loop
from events import AgentEvent
from providers.base import Provider
from tools.agent_tool import AgentTool


class AgentHarness:
    def __init__(
        self,
        provider: Provider,
        tools: list[AgentTool],
        messages: list[dict] | None = None,
        max_loop_iterations: int = 10,
    ) -> None:
        if max_loop_iterations < 1:
            raise ValueError("max_loop_iterations must be at least 1")

        self.provider = provider
        self.tools = tools
        self._messages = messages if messages is not None else []
        self._running = False
        self.max_loop_iterations = max_loop_iterations
        self.system = """
You are a helpful coding assistant. You help users by reading files, executing commands, editing code, and writing new files.
"""
        self._steering_queue: deque[str] = deque()

    @property
    def is_running(self) -> bool:
        return self._running

    def prompt(self, content: str) -> AsyncIterator[AgentEvent]:
        if self._running:
            raise RuntimeError(
                "Agent is already running. Please wait for it to finish."
            )

        self._running = True
        return self._run(content)

    def steer(self, content: str) -> None:
        if not self._running:
            raise RuntimeError("Agent is not running. Cannot steer at this time.")

        self._steering_queue.append(content)

    async def _run(self, content: str) -> AsyncIterator[AgentEvent]:
        try:
            self._messages.append({"role": "user", "content": content})
            async for event in run_agent_loop(
                provider=self.provider,
                tools=self.tools,
                messages=self._messages,
                max_loop_iterations=self.max_loop_iterations,
                system=self.system,
                steering_messages=self._steering_queue,
            ):
                yield event
        finally:
            self._running = False
