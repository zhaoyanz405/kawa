from agent_messages import AgentMessages
from storage.base import BaseSessionStorage
class AgentSession:
    
    def __init__(self, storage: BaseSessionStorage=None):
        self._messages: list[dict] = []
        self.storage = storage

    @classmethod
    def load(cls, storage: BaseSessionStorage):
        instance = cls(storage=storage)
        instance._messages = storage.read_all()
        return instance

    @property
    def messages(self):
        return self._messages
    
    def append(self, message: AgentMessages):
        content = message.to_dict()
        if self.storage:
            self.storage.append(content)
            
        self._messages.append(content)
