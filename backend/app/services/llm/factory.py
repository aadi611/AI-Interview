from functools import lru_cache
from app.services.llm.base import BaseLLMAdapter
from app.config import settings


@lru_cache(maxsize=1)
def get_llm() -> BaseLLMAdapter:
    """Return the configured LLM adapter (singleton)."""
    provider = settings.LLM_PROVIDER.lower()

    if provider == "claude":
        from app.services.llm.claude_adapter import ClaudeAdapter
        return ClaudeAdapter()
    elif provider == "openai":
        from app.services.llm.openai_adapter import OpenAIAdapter
        return OpenAIAdapter()
    elif provider == "ollama":
        from app.services.llm.ollama_adapter import OllamaAdapter
        return OllamaAdapter()
    else:
        raise ValueError(f"Unknown LLM provider: {provider}. Choose from: claude, openai, ollama")
