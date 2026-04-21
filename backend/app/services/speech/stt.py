import io
import tempfile
import os
from openai import AsyncOpenAI
from app.config import settings


class SpeechToTextService:
    def __init__(self):
        self._client = None

    def _get_client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        return self._client

    async def transcribe(self, audio_bytes: bytes, language: str = "en") -> str:
        """Transcribe audio bytes using OpenAI Whisper API."""
        client = self._get_client()

        # Write to a temp file — OpenAI API needs a file-like object with a name
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        try:
            with open(tmp_path, "rb") as audio_file:
                response = await client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language=language,
                )
            return response.text.strip()
        finally:
            os.unlink(tmp_path)

    async def transcribe_stream(self, audio_chunks: list[bytes]) -> str:
        """Transcribe a series of audio chunks joined together."""
        combined = b"".join(audio_chunks)
        return await self.transcribe(combined)


stt_service = SpeechToTextService()
