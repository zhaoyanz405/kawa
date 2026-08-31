from .agent_tool import AgentTool


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


write_to_file_tool = AgentTool(
    name="write_to_file",
    description="Write content to a file.",
    parameters={
        "filename": {
            "type": "string",
            "description": "The file path to write to.",
        },
        "content": {
            "type": "string",
            "description": "The content to write.",
        },
    },
    func=write_to_file,
)
