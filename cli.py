import asyncio
from collections.abc import AsyncIterator

from events import AgentEvent
from harness import AgentHarness


class Reader:
    def __init__(self) -> None:
        self.queue: asyncio.Queue[str] = asyncio.Queue()

    async def start(self) -> None:
        while True:
            try:
                line = await asyncio.to_thread(input, "> ")
            except EOFError:
                await self.queue.put("exit")
                return
            await self.queue.put(line)


class CLI:
    def __init__(self, harness: AgentHarness) -> None:
        self.harness = harness
        self.reader = Reader()
        self._reader_task: asyncio.Task[None] | None = None
        self._runner_task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        self._reader_task = asyncio.create_task(self.reader.start())
        try:
            await self.dispatch_loop()
        finally:
            await self._cancel_task(self._runner_task)
            await self._cancel_task(self._reader_task)
            self._runner_task = None
            self._reader_task = None

    async def dispatch_loop(self) -> None:
        while True:
            user_input = await self.reader.queue.get()
            if user_input.lower() in ["exit", "quit"]:
                print("Exiting...")
                break

            while True:
                if self._runner_task is None:
                    iterator = self.harness.prompt(user_input)
                    self._runner_task = asyncio.create_task(
                        self._consume_prompt(iterator)
                    )
                    await asyncio.sleep(0)
                    break

                if self._runner_task.done():
                    await self._finish_runner()
                    continue

                if self.harness.is_running:
                    self.harness.steer(user_input)
                    break

                await self._finish_runner()

    async def _consume_prompt(self, iterator: AsyncIterator[AgentEvent]) -> None:
        async for event in iterator:
            self._print_event(event)

    @staticmethod
    def _print_event(event: AgentEvent) -> None:
        print(event)

    async def _finish_runner(self) -> None:
        if self._runner_task is None:
            return

        task = self._runner_task
        self._runner_task = None
        await task

    @staticmethod
    async def _cancel_task(task: asyncio.Task[None] | None) -> None:
        if task is None:
            return

        if not task.done():
            task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass


if __name__ == "__main__":
    import asyncio

    from providers.deepseek import DeepSeekProvider

    provider = DeepSeekProvider()

    harness = AgentHarness(provider=provider, tools=[], max_loop_iterations=10)
    cli = CLI(harness=harness)
    asyncio.run(cli.start())
