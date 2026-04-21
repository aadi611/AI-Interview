import io
import httpx
from app.config import settings


class TextToSpeechService:
    async def synthesize(self, text: str) -> bytes:
        """Convert text to speech audio bytes (mp3)."""
        provider = settings.TTS_PROVIDER.lower()
        if provider == "openai":
            return await self._openai(text)
        if provider == "elevenlabs":
            return await self._elevenlabs(text)
        return await self._gtts(text)

    async def _openai(self, text: str) -> bytes:
        """OpenAI TTS — fast (~500ms), natural voices."""
        if not settings.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY not set")
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        resp = await client.audio.speech.create(
            model="tts-1",  # lowest latency model
            voice="nova",   # warm, natural female voice
            input=text,
            response_format="mp3",
            speed=1.25,
        )
        return resp.content

    async def _elevenlabs(self, text: str) -> bytes:
        if not settings.ELEVENLABS_API_KEY:
            raise RuntimeError("ELEVENLABS_API_KEY not set")
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{settings.ELEVENLABS_VOICE_ID}"
        headers = {
            "xi-api-key": settings.ELEVENLABS_API_KEY,
            "Content-Type": "application/json",
        }
        payload = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
        }
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.content

    async def _gtts(self, text: str) -> bytes:
        try:
            from gtts import gTTS
        except ImportError:
            raise RuntimeError("gtts not installed. Run: pip install gtts")
        tts = gTTS(text=text, lang="en", slow=False)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        return buf.read()


tts_service = TextToSpeechService()
