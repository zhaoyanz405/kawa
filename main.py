import asyncio
import click
from cli import CLI
from harness import AgentHarness
from providers.deepseek import DeepSeekProvider
from tools import write_to_file_tool
from storage.base import JsonlSessionStorage
from agent_session import AgentSession

@click.command()
@click.option("--session-file", type=click.Path(), help="Path to a session file.")
def main(session_file: str = None) -> None:
    session = None
    if session_file:
        storage = JsonlSessionStorage(session_file)
        session = AgentSession.load(storage)

    harness = AgentHarness(
        provider=DeepSeekProvider(),
        tools=[write_to_file_tool],
        max_loop_iterations=10,
        session=session
    )
    cli = CLI(harness=harness)
    asyncio.run(cli.start())


if __name__ == "__main__":
    main()
