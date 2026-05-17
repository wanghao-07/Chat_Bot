from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_rag_service, get_settings_dep
from app.config import Settings
from app.core.exceptions import AppError, ValidationError
from app.models.db import get_db
from app.models.schemas import DocumentOut
from app.repositories.document_repo import DocumentRepository
from app.services.ingest_service import IngestService
from app.services.rag_service import RAGService

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("/documents", response_model=list[DocumentOut])
async def list_documents(
    tenant_id: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    repo = DocumentRepository(db)
    docs = await repo.list_all(tenant_id=tenant_id)
    return [DocumentOut.model_validate(d) for d in docs]


@router.post("/documents", response_model=DocumentOut)
async def upload_document(
    file: UploadFile = File(...),
    tenant_id: str = "default",
    title: str | None = None,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings_dep),
    rag: RAGService = Depends(get_rag_service),
):
    if not file.filename:
        raise ValidationError("Filename is required")
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise ValidationError("File too large (max 10MB)")
    ingest = IngestService(db, settings, rag)
    doc = await ingest.ingest_file(file.filename, content, tenant_id=tenant_id, title=title)
    return DocumentOut.model_validate(doc)


@router.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: str,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings_dep),
    rag: RAGService = Depends(get_rag_service),
):
    ingest = IngestService(db, settings, rag)
    await ingest.delete_document(doc_id)
    return {"ok": True, "doc_id": doc_id}
