"""
Admin-only endpoints. All routes require is_admin=True on the authenticated user.
"""
import asyncio
import mimetypes
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Iterable

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy import delete, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.auth import get_current_admin
from app.config import settings
from app.core.database import get_db
from app.models.session import InterviewSession, InterviewStatus
from app.models.user import User

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(get_current_admin)])

DEFAULT_RECORDING_MEDIA_TYPE = "video/webm"


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


def _recording_filename(url: str | None) -> str | None:
    return url.rsplit("/", 1)[-1] if url else None


@lru_cache(maxsize=1)
def _storage_root() -> Path:
    return Path(settings.STORAGE_LOCAL_PATH).resolve()


def _resolve_recording(filename: str | None) -> Path | None:
    """Return the on-disk path for a bare filename, or None if it is unsafe.

    Rejects empty names, '.', '..', anything containing a path separator,
    and anything that resolves (e.g. via symlink) outside the storage root.
    """
    if not filename or filename in {".", ".."} or Path(filename).name != filename:
        return None
    root = _storage_root()
    path = (root / filename).resolve()
    return path if path.parent == root else None


def _recording_path_or_400(filename: str) -> Path:
    path = _resolve_recording(filename)
    if path is None:
        raise HTTPException(status_code=400, detail="Invalid filename")
    return path


def _unlink_quietly(paths: Iterable[Path]) -> None:
    for path in paths:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass  # best effort; the DB is already the source of truth


async def _remove_recordings(urls: Iterable[str | None]) -> None:
    """Delete recording files off the event loop. Call only after commit."""
    paths = [p for p in (_resolve_recording(_recording_filename(u)) for u in urls) if p]
    if paths:
        await asyncio.to_thread(_unlink_quietly, paths)


async def _get_user_or_404(db: AsyncSession, user_id: str) -> User:
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def _forbid_self(admin: User, user_id: str, action: str) -> None:
    if admin.id == user_id:
        raise HTTPException(status_code=400, detail=f"You cannot {action} your own account")


def _serialize_session(s: InterviewSession, user: User | None = None) -> dict:
    return {
        "id": s.id,
        "user_id": s.user_id,
        "user_name": user.name if user else None,
        "user_email": user.email if user else None,
        "domain": s.domain,
        "difficulty": s.difficulty,
        "status": s.status,
        "mode": s.mode,
        "evaluation": s.evaluation,
        "recording_url": s.recording_url,
        "created_at": _iso(s.created_at),
        "started_at": _iso(s.started_at),
        "completed_at": _iso(s.completed_at),
    }


def _serialize_user(u: User, session_count: int = 0) -> dict:
    return {
        "id": u.id,
        "name": u.name,
        "email": u.email,
        "is_admin": bool(u.is_admin),
        "created_at": _iso(u.created_at),
        "session_count": session_count,
    }


def _sessions_with_users():
    return (
        select(InterviewSession, User)
        .join(User, User.id == InterviewSession.user_id)
        .order_by(desc(InterviewSession.created_at))
    )


# --------------------------------------------------------------------------- #
# Stats
# --------------------------------------------------------------------------- #

@router.get("/stats")
async def platform_stats(db: AsyncSession = Depends(get_db)):
    """Aggregate platform statistics across all users (2 queries instead of 5)."""
    total_users = (await db.execute(select(func.count()).select_from(User))).scalar_one()

    rows = (await db.execute(
        select(InterviewSession.domain, InterviewSession.status, func.count())
        .group_by(InterviewSession.domain, InterviewSession.status)
    )).all()

    by_domain: dict = {}
    total = completed = in_progress = 0
    for domain, status, n in rows:
        by_domain[domain] = by_domain.get(domain, 0) + n
        total += n
        if status == InterviewStatus.COMPLETED:
            completed += n
        elif status == InterviewStatus.IN_PROGRESS:
            in_progress += n

    return {
        "total_users": total_users,
        "total_sessions": total,
        "completed_sessions": completed,
        "in_progress_sessions": in_progress,
        "by_domain": by_domain,
    }


# --------------------------------------------------------------------------- #
# Users
# --------------------------------------------------------------------------- #

@router.get("/users")
async def list_users(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    """List users with their session count."""
    counts = (
        select(InterviewSession.user_id, func.count().label("n"))
        .group_by(InterviewSession.user_id)
        .subquery()
    )
    rows = (await db.execute(
        select(User, func.coalesce(counts.c.n, 0))
        .outerjoin(counts, counts.c.user_id == User.id)
        .order_by(desc(User.created_at))
        .limit(limit)
        .offset(offset)
    )).all()
    return [_serialize_user(u, n) for (u, n) in rows]


async def _set_admin(db: AsyncSession, user_id: str, value: bool) -> dict:
    user = await _get_user_or_404(db, user_id)
    if bool(user.is_admin) != value:
        user.is_admin = value
        await db.commit()
    return {"ok": True, "user_id": user.id, "is_admin": value}


@router.post("/users/{user_id}/promote")
async def promote_user(user_id: str, db: AsyncSession = Depends(get_db)):
    return await _set_admin(db, user_id, True)


@router.post("/users/{user_id}/demote")
async def demote_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    _forbid_self(admin, user_id, "demote")
    return await _set_admin(db, user_id, False)


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    _forbid_self(admin, user_id, "delete")
    user = await _get_user_or_404(db, user_id)

    recording_urls = (await db.execute(
        select(InterviewSession.recording_url).where(
            InterviewSession.user_id == user_id,
            InterviewSession.recording_url.is_not(None),
        )
    )).scalars().all()

    await db.execute(delete(InterviewSession).where(InterviewSession.user_id == user_id))
    await db.delete(user)
    await db.commit()

    await _remove_recordings(recording_urls)
    return {"ok": True}


# --------------------------------------------------------------------------- #
# Sessions
# --------------------------------------------------------------------------- #

@router.get("/sessions")
async def list_all_sessions(
    db: AsyncSession = Depends(get_db),
    user_id: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """List sessions across all users. Optionally filter by user_id."""
    stmt = _sessions_with_users()
    if user_id:
        stmt = stmt.where(InterviewSession.user_id == user_id)
    rows = (await db.execute(stmt.limit(limit).offset(offset))).all()
    return [_serialize_session(s, u) for (s, u) in rows]


@router.get("/sessions/{session_id}")
async def get_any_session(session_id: str, db: AsyncSession = Depends(get_db)):
    row = (await db.execute(
        _sessions_with_users().where(InterviewSession.id == session_id)
    )).first()
    if not row:
        raise HTTPException(status_code=404, detail="Session not found")
    s, u = row
    return {**_serialize_session(s, u), "transcript": s.transcript}


@router.delete("/sessions/{session_id}")
async def delete_any_session(session_id: str, db: AsyncSession = Depends(get_db)):
    s = await db.get(InterviewSession, session_id)
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")

    recording_url = s.recording_url
    await db.delete(s)
    await db.commit()

    await _remove_recordings([recording_url])
    return {"ok": True}


# --------------------------------------------------------------------------- #
# Recordings
# --------------------------------------------------------------------------- #

@router.get("/recordings")
async def list_recordings(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """List sessions that have a recording file."""
    rows = (await db.execute(
        _sessions_with_users()
        .where(InterviewSession.recording_url.is_not(None))
        .limit(limit)
        .offset(offset)
    )).all()
    return [
        {**_serialize_session(s, u), "filename": _recording_filename(s.recording_url)}
        for (s, u) in rows
    ]


@router.get("/recordings/{filename}")
async def download_recording(filename: str):
    """Stream any recording file by name."""
    path = _recording_path_or_400(filename)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Recording not found")
    media_type = mimetypes.guess_type(path.name)[0] or DEFAULT_RECORDING_MEDIA_TYPE
    return FileResponse(path, media_type=media_type)


@router.delete("/recordings/{filename}")
async def delete_recording(filename: str, db: AsyncSession = Depends(get_db)):
    path = _recording_path_or_400(filename)

    # Exact filename match only: no LIKE wildcards, no suffix collisions.
    sessions = (await db.execute(
        select(InterviewSession).where(or_(
            InterviewSession.recording_url == filename,
            InterviewSession.recording_url.endswith(f"/{filename}", autoescape=True),
        ))
    )).scalars().all()

    file_exists = await asyncio.to_thread(path.is_file)
    if not sessions and not file_exists:
        raise HTTPException(status_code=404, detail="Recording not found")

    for s in sessions:
        s.recording_url = None
    await db.commit()

    if file_exists:
        await asyncio.to_thread(_unlink_quietly, [path])
    return {"ok": True}