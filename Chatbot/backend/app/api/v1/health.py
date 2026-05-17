from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_settings_dep
from app.config import Settings
from app.models.db import get_db
from app.models.schemas import HealthOut
from app.repositories.document_repo import DocumentRepository

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthOut)
async def health(
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings_dep),
):
    repo = DocumentRepository(db)
    count = await repo.count()
    llm_ok = settings.llm_configured
    status = "ok" if llm_ok else "degraded"
    return HealthOut(
        status=status,
        app_name=settings.app_name,
        rag_enabled=settings.rag_enabled,
        documents_count=count,
        openai_configured=llm_ok,
    )
