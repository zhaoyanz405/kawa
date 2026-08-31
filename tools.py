def write_to_file(filename, content) -> dict:
    """Write content to a file.

    Args:
        filename (str): The name of the file to write to.
        content (str): The content to write into the file.
    Returns:
        dict: A dictionary containing the status and filename.
    """

    with open(filename, "w") as f:
        f.write(content)

    return {"ok": True, "filename": filename}


tools = [
    {
        "type": "function",
        "function": {
            "name": "write_to_file",
            "description": "Write content to a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "The file path to write to.",
                    },
                    "content": {
                        "type": "string",
                        "description": "The content to write.",
                    },
                },
                "required": ["filename", "content"],
                "additionalProperties": False,
            },
        },
    }
]

tool_map = {"write_to_file": write_to_file}
