from dataclasses import dataclass


@dataclass
class AgentMessages:
    role: str
    content: str | None = None

    def to_dict(self):
        return {
            "role": self.role,
            "content": self.content,
        }


@dataclass
class UserMessage(AgentMessages):
    role: str = "user"

    def to_dict(self):
        return super().to_dict()


@dataclass
class AssistantMessage(AgentMessages):
    role: str = "assistant"
    tool_calls: list[dict[str, object]] | None = None

    def to_dict(self):
        base_dict = super().to_dict()
        if self.tool_calls is not None:
            base_dict["tool_calls"] = self.tool_calls
        return base_dict


@dataclass
class ToolMessage(AgentMessages):
    role: str = "tool"
    tool_call_id: str = None
    content: str | None = None

    def to_dict(self):
        base_dict = super().to_dict()
        base_dict["tool_call_id"] = self.tool_call_id
        return base_dict


def load_from_dict(data: dict) -> AgentMessages:
    if not data:
        raise ValueError("Empty data.")

    role = data.get("role")
    if not role:
        raise ValueError("Invalid Data. No role.")

    if role == "user":
        return UserMessage(content=data.get("content"))

    if role == "assistant":
        return AssistantMessage(content=data.get("content"))

    if role == "tool":
        return ToolMessage(
            content=data.get("content"),
            tool_call_id=data.get("tool_call_id"),
        )
