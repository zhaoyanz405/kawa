import asyncio

from agent_messages import (
    AssistantMessage,
    ToolMessage,
    UserMessage,
)
from agent_session import AgentSession
from harness import AgentHarness
from providers.base import AssistantReply
from storage.base import JsonlSessionStorage


class ScriptedProvider:
    def __init__(self, replies: list[AssistantReply]) -> None:
        self.replies = replies
        self.calls: list[list[dict]] = []

    async def complete(
        self, system: str, messages: list[dict], tools: list[dict]
    ) -> AssistantReply:
        del system, tools
        self.calls.append(messages.copy())
        return self.replies.pop(0)


def test_new_session_starts_with_empty_transcript() -> None:
    session = AgentSession()

    assert session.messages == []


def test_session_keeps_one_ordered_transcript_for_all_message_roles() -> None:
    session = AgentSession()
    user_message = UserMessage(content="use echo")
    assistant_message = AssistantMessage(
        content=None,
        tool_calls=[
            {
                "id": "call-1",
                "type": "function",
                "function": {
                    "name": "echo",
                    "arguments": '{"value": "hello"}',
                },
            }
        ],
    )
    tool_message = ToolMessage(
        tool_call_id="call-1",
        content='{"ok": true, "value": "hello"}',
    )

    session.append(user_message)
    session.append(assistant_message)
    session.append(tool_message)

    assert session.messages == [
        user_message.to_dict(),
        assistant_message.to_dict(),
        tool_message.to_dict(),
    ]
    assert [message["role"] for message in session.messages] == [
        "user",
        "assistant",
        "tool",
    ]


def test_harness_writes_prompt_and_reply_to_session() -> None:
    async def scenario() -> None:
        session = AgentSession()
        provider = ScriptedProvider([AssistantReply(content="done")])
        harness = AgentHarness(
            provider=provider,
            tools=[],
            session=session,
        )

        [event async for event in harness.prompt("hello")]

        assert session.messages == [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "done"},
        ]

    asyncio.run(scenario())


def test_same_session_is_used_by_follow_up_prompt() -> None:
    async def scenario() -> None:
        session = AgentSession()
        provider = ScriptedProvider(
            [
                AssistantReply(content="first answer"),
                AssistantReply(content="second answer"),
            ]
        )
        harness = AgentHarness(
            provider=provider,
            tools=[],
            session=session,
        )

        [event async for event in harness.prompt("first question")]
        [event async for event in harness.prompt("second question")]

        assert provider.calls[1] == [
            {"role": "user", "content": "first question"},
            {"role": "assistant", "content": "first answer"},
            {"role": "user", "content": "second question"},
        ]
        assert session.messages == [
            {"role": "user", "content": "first question"},
            {"role": "assistant", "content": "first answer"},
            {"role": "user", "content": "second question"},
            {"role": "assistant", "content": "second answer"},
        ]

    asyncio.run(scenario())


def test_session_append_persists_message_to_storage(tmp_path) -> None:
    session_file = tmp_path / "session.jsonl"
    storage = JsonlSessionStorage(str(session_file))
    session = AgentSession(storage=storage)

    message = UserMessage(content="persist this")
    session.append(message)

    assert storage.read_all() == [message.to_dict()]
    assert session.messages == [message.to_dict()]


def test_loaded_session_continues_persisting_to_the_same_storage(tmp_path) -> None:
    session_file = tmp_path / "session.jsonl"
    storage = JsonlSessionStorage(str(session_file))
    original = AgentSession(storage=storage)
    original.append(UserMessage(content="first"))

    loaded = AgentSession.load(storage)
    second = AssistantMessage(content="second")
    loaded.append(second)

    assert loaded.messages == [
        {"role": "user", "content": "first"},
        second.to_dict(),
    ]
    assert storage.read_all() == loaded.messages
