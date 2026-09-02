import asyncio


def test_cli_start(monkeypatch, capsys):
    inputs = iter(["Hello", "exit"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    class MockHarness:
        def __init__(self) -> None:
            self._running = False

        @property
        def is_running(self) -> bool:
            return self._running

        def prompt(self, content):
            self._running = True

            async def stream():
                try:
                    yield f"Mock response to: {content}"
                finally:
                    self._running = False

            return stream()

        def steer(self, content):
            raise AssertionError("steering was not expected in this test")

    harness = MockHarness()
    from cli import CLI

    cli = CLI(harness=harness)

    result = asyncio.run(cli.start())

    assert result is None
    assert harness.is_running is False
    assert "Exiting..." in capsys.readouterr().out
