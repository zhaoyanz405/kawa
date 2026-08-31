from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict[str, object]


@dataclass
class AssistantReply:
    content: str | None
    tool_calls: list[ToolCall] = field(default_factory=list)


class Provider(Protocol):
    async def complete(
        self, system: str, messages: list[dict], tools: list[dict]
    ) -> AssistantReply: ...
