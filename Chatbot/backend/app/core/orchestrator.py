import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.core.prompts import RAG_CONTEXT_TEMPLATE, format_rag_chunks
from app.repositories.session_repo import SessionRepository
from app.services.config_service import ConfigService
from app.services.llm_service import LLMService
from app.services.memory_service import MemoryService
from app.core.exceptions import LLMError
from app.services.rag_service import RAGService

logger = logging.getLogger(__name__)


class ChatOrchestrator:
    def __init__(
        self,
        db: AsyncSession,
        settings: Settings,
        llm: LLMService,
        rag: RAGService,
        config: ConfigService,
    ):
        self.settings = settings
        self.llm = llm
        self.rag = rag
        self.config = config
        self.repo = SessionRepository(db)
        self.memory = MemoryService(self.repo, settings)

    async def chat(
        self,
        message: str,
        session_id: str | None,
        tenant_id: str = "default",
        use_rag: bool | None = None,
    ) -> dict:
        if session_id:
            session = await self.repo.get(session_id)
            if not session:
                from app.core.exceptions import NotFoundError

                raise NotFoundError("Session not found")
        else:
            session = await self.repo.create(tenant_id=tenant_id)
            session_id = session.id

        history = await self.memory.load_history(session_id)
        sources: list[dict] = []
        rag_requested = use_rag if use_rag is not None else self.settings.rag_enabled
        has_kb = self.rag.has_knowledge_base(tenant_id)
        rag_enabled = rag_requested and has_kb

        messages: list[dict[str, str]] = [
            {"role": "system", "content": self.config.get_system_prompt()},
        ]

        chunks: list[dict] = []
        if rag_enabled:
            try:
                chunks = await self.rag.retrieve(message, tenant_id=tenant_id)
            except Exception as e:
                msg = getattr(e, "message", str(e))
                logger.warning("RAG retrieve failed, chat continues without KB: %s", msg)
                chunks = []
        elif rag_requested and not has_kb:
            logger.debug("RAG skipped: no indexed documents for tenant=%s", tenant_id)

        sources = [
            {
                "doc_title": c.get("doc_title"),
                "doc_id": c.get("doc_id"),
                "score": c.get("score"),
                "text_preview": (c.get("text") or "")[:200],
            }
            for c in chunks
        ]
        if chunks:
            rag_content = RAG_CONTEXT_TEMPLATE.format(
                retrieved_chunks=format_rag_chunks(chunks)
            )
            messages.append({"role": "system", "content": rag_content})
        elif rag_requested and has_kb:
            messages.append(
                {
                    "role": "system",
                    "content": (
                        "知识库中未检索到与问题直接相关的段落。"
                        "请明确告知用户文档中无此信息，不要编造政策或数字。"
                    ),
                }
            )

        messages.extend(history)
        messages.append({"role": "user", "content": message})

        reply, usage = await self.llm.chat(messages)
        await self.memory.save_turn(session_id, message, reply)

        handoff = "[HANDOFF]" in reply
        logger.info(
            "Chat session=%s tenant=%s rag=%s sources=%d tokens=%d handoff=%s",
            session_id,
            tenant_id,
            rag_enabled,
            len(sources),
            usage.get("total_tokens", 0),
            handoff,
        )

        return {
            "session_id": session_id,
            "reply": reply,
            "sources": sources,
            "handoff": handoff,
            "usage": usage,
        }
