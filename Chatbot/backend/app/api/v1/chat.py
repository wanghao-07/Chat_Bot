import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_config_service, get_llm_service, get_rag_service, get_settings_dep
from app.config import Settings
from app.core.exceptions import AppError
from app.core.orchestrator import ChatOrchestrator
from app.models.db import get_db
from app.models.schemas import ChatRequest, ChatResponse
from app.services.config_service import ConfigService
from app.services.llm_service import LLMService
from app.services.rag_service import RAGService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings_dep),
    llm: LLMService = Depends(get_llm_service),
    rag: RAGService = Depends(get_rag_service),
    config: ConfigService = Depends(get_config_service),
):
    try:
        orchestrator = ChatOrchestrator(db, settings, llm, rag, config)
        result = await orchestrator.chat(
            message=body.message.strip(),
            session_id=body.session_id,
            tenant_id=body.tenant_id,
            use_rag=body.use_rag,
        )
        return ChatResponse(
            session_id=result["session_id"],
            reply=result["reply"],
            sources=result["sources"],
            handoff=result["handoff"],
        )
    except AppError:
        raise
    except Exception as e:
        logger.exception("Chat endpoint error")
        raise AppError("An unexpected error occurred", code="INTERNAL_ERROR", status_code=500) from e
