from typing import AsyncIterator
import httpx
import json
from app.services.llm.base import BaseLLMAdapter
from app.config import settings


class OllamaAdapter(BaseLLMAdapter):
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.LLM_MODEL or settings.OLLAMA_MODEL

    def _build_prompt(self, messages: list[dict], system: str = "") -> str:
        parts = []
        if system:
            parts.append(f"System: {system}")
        for m in messages:
            role = m["role"].capitalize()
            parts.append(f"{role}: {m['content']}")
        parts.append("Assistant:")
        return "\n".join(parts)

    async def chat(self, messages: list[dict], system: str = "", **kwargs) -> str:
        payload = {
            "model": self.model,
            "prompt": self._build_prompt(messages, system),
            "stream": False,
        }
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(f"{self.base_url}/api/generate", json=payload)
            response.raise_for_status()
            return response.json()["response"]

    async def stream(self, messages: list[dict], system: str = "", **kwargs) -> AsyncIterator[str]:
        payload = {
            "model": self.model,
            "prompt": self._build_prompt(messages, system),
            "stream": True,
        }
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream("POST", f"{self.base_url}/api/generate", json=payload) as resp:
                async for line in resp.aiter_lines():
                    if line:
                        data = json.loads(line)
                        if token := data.get("response"):
                            yield token

    async def embed(self, text: str) -> list[float]:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self.model, "prompt": text},
            )
            response.raise_for_status()
            return response.json()["embedding"]
