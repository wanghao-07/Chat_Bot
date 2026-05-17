from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import KnowledgeDocument


class DocumentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        filename: str,
        title: str,
        file_path: str,
        tenant_id: str = "default",
    ) -> KnowledgeDocument:
        doc = KnowledgeDocument(
            filename=filename,
            title=title,
            file_path=file_path,
            tenant_id=tenant_id,
            status="processing",
        )
        self.db.add(doc)
        await self.db.flush()
        return doc

    async def get(self, doc_id: str) -> KnowledgeDocument | None:
        result = await self.db.execute(
            select(KnowledgeDocument).where(KnowledgeDocument.id == doc_id)
        )
        return result.scalar_one_or_none()

    async def list_all(self, tenant_id: str | None = None) -> list[KnowledgeDocument]:
        q = select(KnowledgeDocument).order_by(KnowledgeDocument.created_at.desc())
        if tenant_id:
            q = q.where(KnowledgeDocument.tenant_id == tenant_id)
        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def count(self) -> int:
        result = await self.db.execute(select(func.count()).select_from(KnowledgeDocument))
        return result.scalar() or 0

    async def delete(self, doc: KnowledgeDocument) -> None:
        await self.db.delete(doc)

    async def update_status(
        self,
        doc: KnowledgeDocument,
        status: str,
        chunk_count: int = 0,
        error_message: str | None = None,
    ) -> KnowledgeDocument:
        doc.status = status
        doc.chunk_count = chunk_count
        doc.error_message = error_message
        await self.db.flush()
        return doc
