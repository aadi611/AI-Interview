from typing import AsyncIterator
from openai import AsyncOpenAI
from app.services.llm.base import BaseLLMAdapter
from app.config import settings


class OpenAIAdapter(BaseLLMAdapter):
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.LLM_MODEL or settings.OPENAI_MODEL

    async def chat(self, messages: list[dict], system: str = "", **kwargs) -> str:
        full_messages = ([{"role": "system", "content": system}] if system else []) + messages
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=full_messages,
            # Keep replies tight so LLM + TTS round-trip stays snappy.
            max_tokens=kwargs.get("max_tokens", 400),
        )
        return response.choices[0].message.content

    async def stream(self, messages: list[dict], system: str = "", **kwargs) -> AsyncIterator[str]:
        full_messages = ([{"role": "system", "content": system}] if system else []) + messages
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=full_messages,
            stream=True,
            max_tokens=kwargs.get("max_tokens", 2048),
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    async def embed(self, text: str) -> list[float]:
        response = await self.client.embeddings.create(
            input=text,
            model="text-embedding-3-small",
        )
        return response.data[0].embedding
