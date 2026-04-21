from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pathlib import Path

from app.core.database import get_db
from app.models.session import InterviewSession
from app.models.user import User
from app.api.routes.auth import get_current_user
from app.services.recording.handler import recording_handler
from app.config import settings

router = APIRouter(prefix="/recordings", tags=["recordings"])


@router.post("/{session_id}/upload")
async def upload_recording(
    session_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(InterviewSession).where(
            InterviewSession.id == session_id,
            InterviewSession.user_id == user.id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    data = await file.read()
    ext = file.filename.split(".")[-1] if "." in file.filename else "webm"
    url = await recording_handler.save(session_id, data, ext)

    session.recording_url = url
    await db.commit()
    return {"url": url}


@router.get("/{filename}")
async def serve_recording(
    filename: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Block path traversal and require the caller to either own the session
    # or be an admin before streaming the file.
    safe = Path(filename).name
    if safe != filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    result = await db.execute(
        select(InterviewSession).where(InterviewSession.recording_url.like(f"%{safe}"))
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Recording not found")
    if session.user_id != user.id and not user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized for this recording")

    path = Path(settings.STORAGE_LOCAL_PATH) / safe
    if not path.exists():
        raise HTTPException(status_code=404, detail="Recording file missing")
    return FileResponse(path, media_type="video/webm")
