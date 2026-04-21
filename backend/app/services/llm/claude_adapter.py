from typing import AsyncIterator
import anthropic
from app.services.llm.base import BaseLLMAdapter
from app.config import settings


class ClaudeAdapter(BaseLLMAdapter):
    def __init__(self):
        self.client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.LLM_MODEL or settings.CLAUDE_MODEL

    async def chat(self, messages: list[dict], system: str = "", **kwargs) -> str:
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", 2048),
            system=system,
            messages=messages,
        )
        return response.content[0].text

    async def stream(self, messages: list[dict], system: str = "", **kwargs) -> AsyncIterator[str]:
        async with self.client.messages.stream(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", 2048),
            system=system,
            messages=messages,
        ) as stream:
            async for text in stream.text_stream:
                yield text

    async def embed(self, text: str) -> list[float]:
        # Claude doesn't have embeddings — fall back to a simple hash-based stub
        # In production, swap with voyage-ai or openai embeddings
        raise NotImplementedError("Use a dedicated embedding model for Claude projects")
