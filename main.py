import os
from openai import OpenAI
import asyncio
import json


max_loop_iterations = 10  # Set a maximum number of iterations to prevent infinite loops
system = """
You are a helpful coding assistant. You help users by reading files, executing commands, editing code, and writing new files.
"""

messages = []
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
                        "description": "The file path to write to."
                    },
                    "content": {
                        "type": "string",
                        "description": "The content to write."
                    }
                },
                "required": ["filename", "content"],
                "additionalProperties": False
            }
        }
    }
]



LLM_ENDPOINT = "https://api.deepseek.com/"
LLM_API_KEY = os.environ.get("DEEPSEEK_API_KEY")

client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_ENDPOINT)


def get_assistant_response(system, messages):
    response = client.chat.completions.create(
        model="deepseek-v4-flash",
        messages=[
            {"role": "system", "content": system},
            *messages
        ],
        tools=tools,
    )
    return response

def write_to_file(filename, content) -> dict:
    """Write content to a file.
    
    Args:
        filename (str): The name of the file to write to.
        content (str): The content to write into the file.
    Returns:
        dict: A dictionary containing the status and filename.
    """
    
    with open(filename, 'w') as f:
        f.write(content)

    return {"ok": True, "filename": filename}


async def call_provider(system, messages, tools):
    print(f"Calling provider with system: {system}, messages: {messages} and tools: {tools}")
    return get_assistant_response(system, messages)


tool_map = {
    "write_to_file": write_to_file
}

async def run_agent_loop(messages=messages):
    for _ in range(max_loop_iterations):
        response = await call_provider(system, messages, tools)
        if not response:
            print("No response from provider.")
            break

        message = response.choices[0].message
        tool_calls = message.tool_calls or []

        if not tool_calls:
            print(message.content)
            break

        messages.append(message.model_dump(exclude_none=True))

        for call in tool_calls:
            tool_id = call.id
            tool_name = call.function.name
            tool_args = json.loads(call.function.arguments)

            tool = tool_map.get(tool_name)
            if tool:
                result = tool(**tool_args)
                print(f"Tool {tool_name} called with arguments {tool_args}. Result: {result}")
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_id,
                    "content": json.dumps(result, ensure_ascii=False),
                })
            else:
                print(f"Tool {tool_name} not found.")
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_id,
                    "content": json.dumps(
                        {"error": f"Tool {tool_name} not found."},
                        ensure_ascii=False,
                    ),
                })


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_agent_loop([{"role": "user", "content": "创建一个 test.txt文件，内容为 'Hello, World!'"}]))  # Example initial message to create a file
