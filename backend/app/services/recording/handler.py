import os
import uuid
import aiofiles
from pathlib import Path
from app.config import settings


class RecordingHandler:
    async def save(self, session_id: str, data: bytes, ext: str = "webm") -> str:
        """Persist recording data and return its URL/path."""
        if settings.STORAGE_BACKEND == "s3":
            return await self._save_s3(session_id, data, ext)
        return await self._save_local(session_id, data, ext)

    async def _save_local(self, session_id: str, data: bytes, ext: str) -> str:
        storage_dir = Path(settings.STORAGE_LOCAL_PATH)
        storage_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{session_id}.{ext}"
        path = storage_dir / filename
        async with aiofiles.open(path, "wb") as f:
            await f.write(data)
        return f"/recordings/{filename}"

    async def _save_s3(self, session_id: str, data: bytes, ext: str) -> str:
        try:
            import aioboto3
        except ImportError:
            raise RuntimeError("aioboto3 not installed. Run: pip install aioboto3")
        session = aioboto3.Session(
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
        )
        key = f"recordings/{session_id}.{ext}"
        async with session.client("s3") as s3:
            await s3.put_object(Bucket=settings.AWS_BUCKET_NAME, Key=key, Body=data)
        return f"https://{settings.AWS_BUCKET_NAME}.s3.amazonaws.com/{key}"

    async def get_url(self, session_id: str) -> str | None:
        if settings.STORAGE_BACKEND == "local":
            path = Path(settings.STORAGE_LOCAL_PATH) / f"{session_id}.webm"
            return f"/recordings/{session_id}.webm" if path.exists() else None
        return None


recording_handler = RecordingHandler()
