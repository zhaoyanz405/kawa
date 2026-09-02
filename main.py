import asyncio

from cli import CLI
from harness import AgentHarness
from providers.deepseek import DeepSeekProvider
from tools import write_to_file_tool


def main() -> None:
    provider = DeepSeekProvider()

    harness = AgentHarness(
        provider=provider,
        tools=[write_to_file_tool],
        max_loop_iterations=10,
    )
    cli = CLI(harness=harness)
    asyncio.run(cli.start())


if __name__ == "__main__":
    main()
