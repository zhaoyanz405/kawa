import json
import os

from openai import AsyncOpenAI

from providers.base import AssistantReply, ToolCall


class DeepSeekProvider:
    def __init__(self, api_key=None, model="deepseek-v4-flash"):
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        self.base_url = os.environ.get("DEEPSEEK_API_BASE_URL", "https://api.deepseek.com/v1")
        self.model = model
        self.client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)

    async def complete(
        self, system: str, messages: list[dict], tools: list[dict]
    ) -> AssistantReply:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system}] + messages,
            tools=tools,
            timeout=60,
        )

        message = response.choices[0].message
        calls = [
            ToolCall(
                id=call.id,
                name=call.function.name,
                arguments=json.loads(call.function.arguments),
            )
            for call in message.tool_calls or []
        ]
        return AssistantReply(
            content=response.choices[0].message.content, tool_calls=calls
        )
