from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # App
    APP_NAME: str = "AI Interview Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production"
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]
    # Email of the user automatically promoted to admin on startup / registration.
    ADMIN_EMAIL: Optional[str] = None

    # LLM Provider - change to "claude" or "ollama" as needed
    LLM_PROVIDER: str = "openai"
    LLM_MODEL: Optional[str] = None  # optional override; falls back to provider default

    # OpenAI (default)
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4.5-preview"  # update to your model ID, e.g. gpt-4.1, o3

    # Claude (Anthropic)
    ANTHROPIC_API_KEY: Optional[str] = None
    CLAUDE_MODEL: str = "claude-sonnet-4-6"

    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_interview"

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # Storage (recordings)
    STORAGE_BACKEND: str = "local"  # "local" or "s3"
    STORAGE_LOCAL_PATH: str = "./recordings"
    AWS_BUCKET_NAME: Optional[str] = None
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"

    # Speech
    WHISPER_MODEL: str = "base"  # base, small, medium, large
    TTS_PROVIDER: str = "elevenlabs"  # "elevenlabs" or "gtts"
    ELEVENLABS_API_KEY: Optional[str] = None
    ELEVENLABS_VOICE_ID: str = "21m00Tcm4TlvDq8ikWAM"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
