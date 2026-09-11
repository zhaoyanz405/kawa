import json

import pytest

from agent_messages import UserMessage
from main import open_session


@pytest.mark.parametrize("filename", ["test.jsonl", "abc/test.jsonl"])
def test_open_session(tmp_cwd, filename):

    session = open_session(filename)
    assert session.storage.name == filename

    test_msg = UserMessage(content="test")
    session.append(test_msg)
    assert session.messages == [test_msg.to_dict()]


def test_open_session_in_mem():
    session = open_session("")
    assert session.storage is None

    test_msg = UserMessage(content="test")
    session.append(test_msg)
    assert session.messages == [test_msg.to_dict()]


def test_open_session_from_exist_file(tmp_cwd):
    session_file = tmp_cwd / "test.jsonl"
    test_msgs = [
        json.dumps({"id": "1", "parent_id": "0", "role": "user", "content": "hi"})
        + "\n",
        json.dumps(
            {
                "id": "2",
                "parent_id": "1",
                "role": "assistant",
                "content": "Hello! How can I help you today?",
            }
        )
        + "\n",
    ]
    with open(session_file, "w") as f:
        f.writelines(test_msgs)

    session = open_session(str(session_file))
    assert session.messages == [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "Hello! How can I help you today?"},
    ]
