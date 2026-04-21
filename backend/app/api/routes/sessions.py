from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.models.session import InterviewSession, InterviewStatus
from app.models.user import User
from app.api.routes.auth import get_current_user
from app.domains.registry import list_domains, get_domain

router = APIRouter(prefix="/sessions", tags=["sessions"])


class CreateSessionRequest(BaseModel):
    domain: str
    difficulty: str = "medium"
    mode: str = "hybrid"  # legacy field — always hybrid now (voice + chat together)


@router.get("/domains")
async def get_domains():
    return list_domains()


@router.post("/")
async def create_session(
    body: CreateSessionRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    get_domain(body.domain)  # validates domain exists

    session = InterviewSession(
        user_id=user.id,
        domain=body.domain,
        difficulty=body.difficulty,
        mode=body.mode,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return _serialize(session)


@router.get("/")
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(InterviewSession)
        .where(InterviewSession.user_id == user.id)
        .order_by(desc(InterviewSession.created_at))
        .limit(50)
    )
    return [_serialize(s) for s in result.scalars().all()]


@router.get("/{session_id}")
async def get_session(
    session_id: str,
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
    return _serialize(session)


@router.delete("/{session_id}")
async def cancel_session(
    session_id: str,
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
    session.status = InterviewStatus.CANCELLED
    await db.commit()
    return {"ok": True}


def _serialize(s: InterviewSession) -> dict:
    return {
        "id": s.id,
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
