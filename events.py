from dataclasses import dataclass
from typing import Literal

EndReason = Literal["completed", "max_iterations", "cancelled"]


@dataclass(frozen=True)
class AgentStartEvent:
    type: str = "agent_start"


@dataclass(frozen=True)
class MessageEvent:
    role: str
    content: str | None
    type: str = "message"


@dataclass(frozen=True)
class ToolExecutionStartEvent:
    name: str
    arguments: dict[str, object]
    type: str = "tool_execution_start"


@dataclass(frozen=True)
class ToolExecutionEndEvent:
    name: str
    result: dict[str, object]
    type: str = "tool_execution_end"


@dataclass(frozen=True)
class AgentEndEvent:
    reason: EndReason = "completed"
    type: str = "agent_end"


AgentEvent = (
    AgentStartEvent
    | MessageEvent
    | ToolExecutionStartEvent
    | ToolExecutionEndEvent
    | AgentEndEvent
)
