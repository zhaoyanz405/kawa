import json
from agent_messages import AssistantMessage, UserMessage
from session.agent_session import AgentSession
from session.entry import SessionEntry as Entry
from storage.base import JsonlSessionStorage


def test_agent_session_append():
    session = AgentSession()
    assert session.active_leaf_id is None

    session.append(UserMessage(content="Hello"))
    assert len(session.messages) > 0
    assert session.active_leaf_id is not None

    old_id = session.active_leaf_id

    session.append(AssistantMessage(content="Yes, what can I help you?"))
    assert len(session.messages) == 2
    assert Entry.generate_id(old_id) == session.active_leaf_id

    msg0 = session.messages[0]
    assert "id" not in msg0
    assert "parent_id" not in msg0
    assert "Hello" == msg0.get("content")

    msg1 = session.messages[1]
    assert "id" not in msg1
    assert "parent_id" not in msg1
    assert "Yes, what can I help you?" == msg1.get("content")


def test_agent_session_load(tmp_cwd):

    entry1 = Entry(message=UserMessage(content="hello"))
    entry2 = Entry(parent_id=entry1.id, message=AssistantMessage(content="Yes?"))

    data1 = entry1.to_dict()
    data2 = entry2.to_dict()

    msg1 = json.dumps(data1)
    msg2 = json.dumps(data2)

    with open("test.jsonl", "w") as f:
        f.write(str(msg1) + "\n")
        f.write(str(msg2) + "\n")

    storage = JsonlSessionStorage("test.jsonl")
    session = AgentSession.load(storage=storage)
    assert session.messages == [
        entry1.agent_message.to_dict(),
        entry2.agent_message.to_dict(),
    ]
