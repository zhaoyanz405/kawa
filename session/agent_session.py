from agent_messages import AgentMessages, load_from_dict
from storage.base import BaseSessionStorage

from .entry import SessionEntry as Entry


class AgentSession:
    def __init__(self, storage: BaseSessionStorage = None):
        self.storage = storage
        self.active_leaf_id: str | None = None
        self._entries_by_id: dict[str, Entry] = {}

    @classmethod
    def load(cls, storage: BaseSessionStorage):
        instance = cls(storage=storage)
        for msg in storage.read_all():
            id = msg.get("id")
            if not id:
                raise ValueError("msg id is missing")

            parent_id = msg.get("parent_id")
            if parent_id is not None and parent_id not in instance._entries_by_id:
                raise ValueError(f"Parent entry {parent_id} not found.")

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

        visited = set()
        while p is not None:
            if p not in visited:
                visited.add(p)
            else:
                raise ValueError("invalid structure due to a circular reference")

            v = self._entries_by_id.get(p)
            if not v:
                raise ValueError(f"entry {p} not found.")

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
        self.checkout(entry_id=entry.id)
        return entry.id

    def set_entry(self, entry: Entry):
        if entry.id in self._entries_by_id:
            raise ValueError(f"Duplicate Entry {entry.id} Data")
        self._entries_by_id[entry.id] = entry

    def checkout(self, entry_id):
        if not entry_id:
            raise ValueError("entry id can't be empty.")

        if entry_id not in self._entries_by_id:
            raise ValueError(f"entry {entry_id} not found.")

        self.active_leaf_id = entry_id
