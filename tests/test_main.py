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
        json.dumps({"role": "user", "content": "hello"}) + "\n",
        json.dumps({"role": "assistant", "content": "hello"}) + "\n",
    ]
    with open(session_file, "w") as f:
        f.writelines(test_msgs)

    session = open_session(str(session_file))
    assert session.messages == [json.loads(message) for message in test_msgs]
