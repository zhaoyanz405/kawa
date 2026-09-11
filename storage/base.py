import logging
import json

class BaseSessionStorage:
    
    def __init__(self, filename: str):
        self.name = filename
    
    def append(self, message: dict):
        raise NotImplementedError("SessionStorage is an abstract class. Please implement the append method in a subclass.")
    
    def read_all(self) -> list[dict]:
        raise NotImplementedError("SessionStorage is an abstract class. Please implement the read_all method in a subclass.")


class JsonlSessionStorage(BaseSessionStorage):
    
    def append(self, message: dict):
        with open(self.name, "a") as f:
            f.write(json.dumps(message) + "\n")
    
    
    def read_all(self) -> list[dict]:
        messages = []
        try:
            with open(self.name, "r") as f:
                for line in f:
                    data = json.loads(line.strip())
                    messages.append(data)
        except FileNotFoundError:
            logging.warning("Session file not found. Starting a new session.")
        return messages
