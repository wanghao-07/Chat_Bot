import logging
import shutil
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.core.exceptions import RAGError, ValidationError
from app.rag.chunker import chunk_text, extract_text_from_file
from app.repositories.document_repo import DocumentRepository
from app.services.rag_service import RAGService

logger = logging.getLogger(__name__)

ALLOWED_SUFFIXES = {".pdf", ".txt", ".md", ".markdown"}


class IngestService:
    def __init__(
        self,
        db: AsyncSession,
        settings: Settings,
        rag: RAGService,
    ):
        self.db = db
        self.settings = settings
        self.rag = rag
        self.doc_repo = DocumentRepository(db)

    async def ingest_file(
        self,
        filename: str,
        content: bytes,
        tenant_id: str = "default",
        title: str | None = None,
    ):
        suffix = Path(filename).suffix.lower()
        if suffix not in ALLOWED_SUFFIXES:
            raise ValidationError(f"Unsupported file type. Allowed: {', '.join(ALLOWED_SUFFIXES)}")

        doc = await self.doc_repo.create(
            filename=filename,
            title=title or Path(filename).stem,
            file_path="",
            tenant_id=tenant_id,
        )
        save_path = self.settings.data_path / "uploads" / f"{doc.id}{suffix}"
        save_path.write_bytes(content)
        doc.file_path = str(save_path)
        await self.db.flush()

        try:
            text = extract_text_from_file(save_path)
            chunks = chunk_text(
                text,
                chunk_size=self.settings.chunk_size,
                overlap=self.settings.chunk_overlap,
            )
            if not chunks:
                raise RAGError("No text could be extracted from document")

            count = await self.rag.index_chunks(tenant_id, doc.id, doc.title, chunks)
            await self.doc_repo.update_status(doc, "ready", chunk_count=count)
            logger.info("Ingested doc_id=%s chunks=%d", doc.id, count)
            return doc
        except Exception as e:
            logger.exception("Ingest failed doc_id=%s", doc.id)
            msg = str(e)
            if hasattr(e, "message"):
                msg = e.message
            await self.doc_repo.update_status(doc, "error", error_message=msg)
            raise RAGError(msg if msg.startswith("阿里云") else f"文档处理失败: {msg}") from e

    async def delete_document(self, doc_id: str) -> None:
        doc = await self.doc_repo.get(doc_id)
        if not doc:
            from app.core.exceptions import NotFoundError

            raise NotFoundError("Document not found")
        self.rag.remove_document(doc.tenant_id, doc.id)
        path = Path(doc.file_path)
        if path.exists():
            path.unlink()
        await self.doc_repo.delete(doc)
        logger.info("Deleted document doc_id=%s", doc_id)
