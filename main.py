import asyncio
import json

from agent_loop import run_agent_loop
from providers.base import Provider
from tools import write_to_file_tool, AgentTool


class AgentHarness:
    def __init__(
        self,
        provider: Provider,
        tools: list[AgentTool],
        messages: list[dict] | None = None,
        max_loop_iterations: int = 10,
    ):
        self.provider = provider
        self.tools = tools
        self._messages = messages if messages is not None else []
        self._running = False
        self.max_loop_iterations = max_loop_iterations
        self.system = """
You are a helpful coding assistant. You help users by reading files, executing commands, editing code, and writing new files.
"""

    async def prompt(self, content: str):
        if self._running:
            raise RuntimeError(
                "Agent is already running. Please wait for it to finish."
            )

        self._messages.append({"role": "user", "content": content})

        self._running = True
        try:
            async for event in run_agent_loop(
                provider=self.provider,
                tools=self.tools,
                messages=self._messages,
                max_loop_iterations=self.max_loop_iterations,
                system=self.system,
            ):
                yield event
        finally:
            self._running = False


class CLI:
    def __init__(self, harness: AgentHarness):
        self.harness = harness
    
    async def start(self) -> str:
        while True:
            print("--------------------------------")
            user_input = input(">: ")
            if user_input.strip():
                async for event in self.harness.prompt(user_input):
                    print(event)


if __name__ == "__main__":
    from providers.deepseek import DeepSeekProvider

    provider = DeepSeekProvider()

    harness = AgentHarness(
        provider=provider, tools=[write_to_file_tool], max_loop_iterations=10
    )
    cli = CLI(harness=harness)
    asyncio.run(cli.start())
