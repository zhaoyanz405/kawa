import json

from storage.base import JsonlSessionStorage


def test_storage_append(tmp_path):
    tmp_file = tmp_path / "session.jsonl"
    storage = JsonlSessionStorage(str(tmp_file))
    message = {"role": "user", "content": "Hello!"}
    storage.append(message)
    message2 = {"role": "assistant", "content": "Hi!"}
    storage.append(message2)

    # Read the file and check if the message was appended
    with open(tmp_file, "r") as f:
        lines = f.readlines()
        assert len(lines) == 2
        assert json.loads(lines[0].strip()) == message
        assert json.loads(lines[1].strip()) == message2


def test_storage_read_all(tmp_path):
    tmp_file = tmp_path / "session.jsonl"
    storage = JsonlSessionStorage(str(tmp_file))
    messages = [
        {"role": "user", "content": "Hello!"},
        {"role": "assistant", "content": "Hi!"},
    ]
    for message in messages:
        storage.append(message)

    read_messages = storage.read_all()
    assert read_messages == messages
