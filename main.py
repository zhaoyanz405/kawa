import asyncio
import os

import click

from agent_session import AgentSession
from cli import CLI
from harness import AgentHarness
from providers.deepseek import DeepSeekProvider
from storage.base import JsonlSessionStorage
from tools import write_to_file_tool


def open_session(filename: str | None) -> AgentSession:
    if filename is not None:
        filename = filename.strip()

    if not filename:
        return AgentSession()

    directory = os.path.dirname(filename)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)

    storage = JsonlSessionStorage(filename)
    session = AgentSession.load(storage)
    return session


@click.command()
@click.option("--session-file", type=click.Path(), help="Path to a session file.")
def main(session_file: str = None) -> None:
    session = open_session(session_file)

    harness = AgentHarness(
        provider=DeepSeekProvider(),
        tools=[write_to_file_tool],
        max_loop_iterations=10,
        session=session,
    )
    cli = CLI(harness=harness)
    asyncio.run(cli.start())


if __name__ == "__main__":
    main()
