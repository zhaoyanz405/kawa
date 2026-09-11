from agent_messages import AgentMessages, load_from_dict
from storage.base import BaseSessionStorage

from .entry import SessionEntry as Entry


class AgentSession:
    def __init__(
        self, storage: BaseSessionStorage = None
    ):
        self.storage = storage
        self.active_leaf_id: str = None
        self._entries_by_id: dict[str, Entry] = {}

    @classmethod
    def load(cls, storage: BaseSessionStorage):
        instance = cls(storage=storage)
        for msg in storage.read_all():
            id = msg.get("id")
            parent_id = msg.get("parent_id")
            agent_msg = load_from_dict(msg)
            entry = Entry(id=id, parent_id=parent_id, message=agent_msg)
            instance.set_entry(entry)
            instance.active_leaf_id = entry.id
        return instance

    @property
    def messages(self):
        if not self.active_leaf_id:
            if not self._entries_by_id:
                return []
            else:
                raise ValueError("data misatched.")

        msgs = []
        p = self.active_leaf_id
        while True:
            v = self._entries_by_id.get(p)
            if not v:
                break

            msgs.append(v.agent_message.to_dict())
            p = v.parent_id

        msgs.reverse()
        return msgs

    def append(self, message: AgentMessages):
        entry = Entry(parent_id=self.active_leaf_id, message=message)
        if self.storage is not None:
            content = entry.to_dict()
            self.storage.append(content)

        self.set_entry(entry)

    def set_entry(self, entry: Entry):
        self._entries_by_id[entry.id] = entry
        self.active_leaf_id = entry.id
