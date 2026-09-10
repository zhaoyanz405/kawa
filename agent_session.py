from agent_messages import AgentMessages

class AgentSession:
    
    def __init__(self):
        self._messages: list[dict] = []
    
    @property
    def messages(self):
        return self._messages
    
    def append(self, message: AgentMessages):
        self._messages.append(message.to_dict())
