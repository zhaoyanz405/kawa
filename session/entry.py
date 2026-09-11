from uuid import uuid4

from agent_messages import AgentMessages


class SessionEntry:
    def __init__(
        self,
        id: str | None = None,
        parent_id: str | None = None,
        message: AgentMessages | None = None,
    ):
        if not id:
            id = str(uuid4())

        self.id = id

        if not parent_id:
            parent_id = ""

        self.parent_id = parent_id
        self.agent_message: AgentMessages = message

    def to_dict(self):
        base = {
            "id": self.id,
            "parent_id": self.parent_id,
        }

        base.update(self.agent_message.to_dict())
        return base
