from abc import ABC, abstractmethod
from typing import AsyncIterator


class BaseLLMAdapter(ABC):
    """Abstract base for all LLM providers."""

    @abstractmethod
    async def chat(self, messages: list[dict], **kwargs) -> str:
        """Send messages and get a complete response."""
        ...

    @abstractmethod
    async def stream(self, messages: list[dict], **kwargs) -> AsyncIterator[str]:
        """Send messages and stream the response token by token."""
        ...

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Return embedding vector for the given text."""
        ...
