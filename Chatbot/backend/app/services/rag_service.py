import logging

from app.config import Settings
from app.rag.vector_store import FaissVectorStore
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class RAGService:
    def __init__(self, settings: Settings, llm: LLMService):
        self.settings = settings
        self.llm = llm

    def _store(self, tenant_id: str) -> FaissVectorStore:
        return FaissVectorStore(self.settings, tenant_id)

    def has_knowledge_base(self, tenant_id: str = "default") -> bool:
        return self._store(tenant_id).has_vectors()

    async def index_chunks(
        self,
        tenant_id: str,
        doc_id: str,
        doc_title: str,
        chunks: list[str],
    ) -> int:
        if not chunks:
            return 0
        embeddings = await self.llm.embed(chunks)
        metadatas = [
            {
                "doc_id": doc_id,
                "doc_title": doc_title,
                "chunk_index": i,
                "text": chunk,
            }
            for i, chunk in enumerate(chunks)
        ]
        store = self._store(tenant_id)
        store.add_with_vectors(embeddings, metadatas)
        return len(chunks)

    async def retrieve(
        self,
        query: str,
        tenant_id: str = "default",
    ) -> list[dict]:
        store = self._store(tenant_id)
        if not store.has_vectors():
            logger.debug("RAG skip: empty knowledge base tenant=%s", tenant_id)
            return []
        query_embeddings = await self.llm.embed([query])
        if not query_embeddings:
            return []
        chunks = store.search(
            query_embeddings[0],
            top_k=self.settings.rag_top_k,
            threshold=self.settings.rag_score_threshold,
        )
        if not chunks and store.has_vectors():
            chunks = store.search(
                query_embeddings[0],
                top_k=min(3, self.settings.rag_top_k),
                threshold=0.0,
            )[:1]
            if chunks:
                logger.info("RAG fallback: using best match for tenant=%s", tenant_id)
        return chunks

    def remove_document(self, tenant_id: str, doc_id: str) -> int:
        store = self._store(tenant_id)
        return store.remove_by_doc_id(doc_id)
