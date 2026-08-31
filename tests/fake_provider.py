from collections.abc import Iterable

from providers.base import AssistantReply


class FakeProvider:
    """Replay scripted replies without touching a real API."""

    def __init__(self, script: Iterable[AssistantReply]) -> None:
        self._script = list(script)
        self.calls: list[list[dict]] = []

    async def complete(
        self,
        system: str,
        messages: list[dict],
        tools: list[dict],
    ) -> AssistantReply:
        del system, tools
        self.calls.append(list(messages))
        if not self._script:
            return AssistantReply(content=None, tool_calls=[])
        return self._script.pop(0)
