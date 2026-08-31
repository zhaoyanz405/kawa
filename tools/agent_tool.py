from collections.abc import Callable


class AgentTool:
    def __init__(
        self,
        name: str,
        description: str,
        parameters: dict[str, object],
        func: Callable[..., dict[str, object]],
    ) -> None:
        self.name = name
        self.description = description
        self.parameters = parameters
        self.func = func

    def input_schema(self) -> dict[str, object]:
        """Return the input schema for the tool."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": self.parameters,
                    "required": list(self.parameters.keys()),
                    "additionalProperties": False,
                },
            },
        }

    def execute(self, kwargs: dict[str, object]) -> dict[str, object]:
        """Execute the tool with the given arguments."""
        return self.func(**kwargs)
