"""
Admin-only endpoints. All routes require is_admin=True on the authenticated user.
"""
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from app.core.database import get_db
from app.models.session import InterviewSession, InterviewStatus
from app.models.user import User
from app.api.routes.auth import get_current_admin
from app.config import settings

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(get_current_admin)])


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
        "created_at": s.created_at.isoformat() if s.created_at else None,
        "started_at": s.started_at.isoformat() if s.started_at else None,
        "completed_at": s.completed_at.isoformat() if s.completed_at else None,
    }


def _serialize_user(u: User, session_count: int = 0) -> dict:
    return {
        "id": u.id,
        "name": u.name,
        "email": u.email,
        "is_admin": bool(u.is_admin),
        "created_at": u.created_at.isoformat() if u.created_at else None,
        "session_count": session_count,
    }


@router.get("/stats")
async def platform_stats(db: AsyncSession = Depends(get_db)):
    """Aggregate platform statistics across all users."""
    total_users = (await db.execute(select(func.count(User.id)))).scalar_one()
    total_sessions = (await db.execute(select(func.count(InterviewSession.id)))).scalar_one()
    completed = (await db.execute(
        select(func.count(InterviewSession.id)).where(
            InterviewSession.status == InterviewStatus.COMPLETED
        )
    )).scalar_one()
    in_progress = (await db.execute(
        select(func.count(InterviewSession.id)).where(
            InterviewSession.status == InterviewStatus.IN_PROGRESS
        )
    )).scalar_one()

    # Sessions per domain
    by_domain_rows = (await db.execute(
        select(InterviewSession.domain, func.count(InterviewSession.id))
        .group_by(InterviewSession.domain)
    )).all()
    by_domain = {row[0]: row[1] for row in by_domain_rows}

    return {
        "total_users": total_users,
        "total_sessions": total_sessions,
        "completed_sessions": completed,
        "in_progress_sessions": in_progress,
        "by_domain": by_domain,
    }


@router.get("/users")
async def list_users(db: AsyncSession = Depends(get_db)):
    """List all users along with their session count."""
    rows = (await db.execute(
        select(User, func.count(InterviewSession.id))
        .outerjoin(InterviewSession, InterviewSession.user_id == User.id)
        .group_by(User.id)
        .order_by(desc(User.created_at))
    )).all()
    return [_serialize_user(u, count) for (u, count) in rows]


@router.post("/users/{user_id}/promote")
async def promote_user(user_id: str, db: AsyncSession = Depends(get_db)):
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_admin = True
    await db.commit()
    return {"ok": True, "user_id": user.id, "is_admin": True}


@router.post("/users/{user_id}/demote")
async def demote_user(user_id: str, db: AsyncSession = Depends(get_db)):
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_admin = False
    await db.commit()
    return {"ok": True, "user_id": user.id, "is_admin": False}


@router.delete("/users/{user_id}")
async def delete_user(user_id: str, db: AsyncSession = Depends(get_db)):
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Clear out sessions first to avoid FK issues.
    await db.execute(
        InterviewSession.__table__.delete().where(InterviewSession.user_id == user_id)
    )
    await db.delete(user)
    await db.commit()
    return {"ok": True}


@router.get("/sessions")
async def list_all_sessions(
    db: AsyncSession = Depends(get_db),
    user_id: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
):
    """List every session across all users. Optionally filter by user_id."""
    stmt = (
        select(InterviewSession, User)
        .join(User, User.id == InterviewSession.user_id)
        .order_by(desc(InterviewSession.created_at))
        .limit(limit)
    )
    if user_id:
        stmt = stmt.where(InterviewSession.user_id == user_id)
    rows = (await db.execute(stmt)).all()
    return [_serialize_session(s, u) for (s, u) in rows]


@router.get("/sessions/{session_id}")
async def get_any_session(session_id: str, db: AsyncSession = Depends(get_db)):
    row = (await db.execute(
        select(InterviewSession, User)
        .join(User, User.id == InterviewSession.user_id)
        .where(InterviewSession.id == session_id)
    )).first()
    if not row:
        raise HTTPException(status_code=404, detail="Session not found")
    s, u = row
    result = _serialize_session(s, u)
    result["transcript"] = s.transcript
    return result


@router.delete("/sessions/{session_id}")
async def delete_any_session(session_id: str, db: AsyncSession = Depends(get_db)):
    s = (await db.execute(
        select(InterviewSession).where(InterviewSession.id == session_id)
    )).scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")

    # Best-effort remove the recording file from disk if present.
    if s.recording_url:
        try:
            filename = s.recording_url.rsplit("/", 1)[-1]
            path = Path(settings.STORAGE_LOCAL_PATH) / filename
            if path.exists():
                path.unlink()
        except Exception:
            pass

    await db.delete(s)
    await db.commit()
    return {"ok": True}


@router.get("/recordings")
async def list_recordings(db: AsyncSession = Depends(get_db)):
    """List every session that has a recording file."""
    rows = (await db.execute(
        select(InterviewSession, User)
        .join(User, User.id == InterviewSession.user_id)
        .where(InterviewSession.recording_url.is_not(None))
        .order_by(desc(InterviewSession.created_at))
    )).all()
    return [
        {
            **_serialize_session(s, u),
            "filename": s.recording_url.rsplit("/", 1)[-1] if s.recording_url else None,
        }
        for (s, u) in rows
    ]


@router.get("/recordings/{filename}")
async def download_recording(filename: str):
    """Admins can stream any recording file by name."""
    # Reject path traversal attempts.
    safe = Path(filename).name
    if safe != filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    path = Path(settings.STORAGE_LOCAL_PATH) / safe
    if not path.exists():
        raise HTTPException(status_code=404, detail="Recording not found")
    return FileResponse(path, media_type="video/webm")


@router.delete("/recordings/{filename}")
async def delete_recording(filename: str, db: AsyncSession = Depends(get_db)):
    safe = Path(filename).name
    if safe != filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    path = Path(settings.STORAGE_LOCAL_PATH) / safe
    if path.exists():
        path.unlink()

    # Clear the recording_url on any matching session row.
    rows = (await db.execute(
        select(InterviewSession).where(InterviewSession.recording_url.like(f"%{safe}"))
    )).scalars().all()
    for s in rows:
        s.recording_url = None
    await db.commit()
    return {"ok": True}
