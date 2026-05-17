from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.db import get_db
from app.models.schemas import MessageOut, SessionOut
from app.repositories.session_repo import SessionRepository

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("/{session_id}", response_model=SessionOut)
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    repo = SessionRepository(db)
    session = await repo.get(session_id)
    if not session:
        raise NotFoundError("Session not found")
    return SessionOut(
        id=session.id,
        tenant_id=session.tenant_id,
        created_at=session.created_at,
        messages=[MessageOut.model_validate(m) for m in session.messages],
    )
