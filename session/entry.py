from agent_messages import AgentMessages


class SessionEntry:
    def __init__(
        self, parent_id: str | None = None, message: AgentMessages | None = None
    ):
        if not parent_id:
            self.parent_id = self.generate_id()
        else:
            self.parent_id = parent_id

        self.id = self.generate_id(self.parent_id)
        self.agent_message: AgentMessages = message

    @classmethod
    def generate_id(cls, parent_id=None):
        if not parent_id:
            return "0"
        return str(int(parent_id) + 1)

    def to_dict(self):
        base = {
            "id": self.id,
            "parent_id": self.parent_id,
        }

        base.update(self.agent_message.to_dict())
        return base
