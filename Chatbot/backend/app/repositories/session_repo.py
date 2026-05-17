from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.message import ChatMessage
from app.models.session import ChatSession


class SessionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, tenant_id: str = "default") -> ChatSession:
        session = ChatSession(tenant_id=tenant_id)
        self.db.add(session)
        await self.db.flush()
        return session

    async def get(self, session_id: str) -> ChatSession | None:
        result = await self.db.execute(
            select(ChatSession)
            .where(ChatSession.id == session_id)
            .options(selectinload(ChatSession.messages))
        )
        return result.scalar_one_or_none()

    async def add_message(self, session_id: str, role: str, content: str) -> ChatMessage:
        msg = ChatMessage(session_id=session_id, role=role, content=content)
        self.db.add(msg)
        await self.db.flush()
        return msg

    async def get_recent_messages(
        self, session_id: str, max_turns: int
    ) -> list[ChatMessage]:
        """Return last N*2 messages (user+assistant pairs)."""
        limit = max_turns * 2
        result = await self.db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .where(ChatMessage.role.in_(["user", "assistant"]))
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
        )
        rows = list(result.scalars().all())
        rows.reverse()
        return rows
