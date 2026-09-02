import asyncio

from harness import AgentHarness
from providers.base import AssistantReply, ToolCall
from tools.agent_tool import AgentTool


class FakeProvider:
    def __init__(self, replies: list[AssistantReply]) -> None:
        self._replies = replies
        self.calls = 0

    async def complete(
        self, system: str, messages: list[dict], tools: list[dict]
    ) -> AssistantReply:
        if self.calls >= len(self._replies):
            raise AssertionError("FakeProvider ran out of replies")

        reply = self._replies[self.calls]
        self.calls += 1
        return reply


def echo(value: str) -> dict[str, object]:
    return {"ok": True, "value": value}


echo_tool = AgentTool(
    name="echo",
    description="Echo a value.",
    parameters={"value": {"type": "string"}},
    func=echo,
)


async def main() -> None:
    provider = FakeProvider(
        [
            AssistantReply(
                content=None,
                tool_calls=[ToolCall("call-1", "echo", {"value": "hello"})],
            ),
            AssistantReply(content="The tool returned hello."),
        ]
    )
    harness = AgentHarness(
        provider=provider,
        tools=[echo_tool],
        max_loop_iterations=3,
    )

    async for event in harness.prompt("use the echo tool"):
        print(event)


if __name__ == "__main__":
    asyncio.run(main())
