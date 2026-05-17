import json
import logging
from pathlib import Path

import faiss
import numpy as np

from app.config import Settings

logger = logging.getLogger(__name__)


class FaissVectorStore:
    """FAISS IndexFlatIP + JSON metadata (includes stored vectors for safe deletes)."""

    def __init__(self, settings: Settings, tenant_id: str = "default"):
        self.settings = settings
        self.tenant_id = tenant_id
        self.index_path = settings.data_path / "faiss" / f"{tenant_id}.index"
        self.meta_path = settings.data_path / "faiss" / f"{tenant_id}.meta.json"
        self._index: faiss.IndexFlatIP | None = None
        self._metadata: list[dict] = []

    def has_vectors(self) -> bool:
        self._load()
        return self._index is not None and self._index.ntotal > 0

    def _load(self) -> None:
        if self._index is not None:
            return
        if self.index_path.exists() and self.meta_path.exists():
            self._index = faiss.read_index(str(self.index_path))
            self._metadata = json.loads(self.meta_path.read_text(encoding="utf-8"))
            logger.info(
                "Loaded FAISS tenant=%s vectors=%d", self.tenant_id, self._index.ntotal
            )
        else:
            self._metadata = []
            self._index = None

    def _persist(self) -> None:
        if self._index is not None and self._index.ntotal > 0:
            faiss.write_index(self._index, str(self.index_path))
        elif self.index_path.exists():
            self.index_path.unlink()
        if self._metadata:
            self.meta_path.write_text(
                json.dumps(self._metadata, ensure_ascii=False), encoding="utf-8"
            )
        elif self.meta_path.exists():
            self.meta_path.unlink()

    def _rebuild_index(self) -> None:
        vectors = [m.get("_vector") for m in self._metadata]
        if not vectors or any(v is None for v in vectors):
            self._index = None
            self._persist()
            return
        arr = np.array(vectors, dtype=np.float32)
        dim = arr.shape[1]
        faiss.normalize_L2(arr)
        self._index = faiss.IndexFlatIP(dim)
        self._index.add(arr)
        self._persist()

    def add_with_vectors(self, embeddings: list[list[float]], metadatas: list[dict]) -> None:
        self._load()
        for emb, meta in zip(embeddings, metadatas):
            entry = {**meta, "_vector": emb}
            self._metadata.append(entry)
        self._rebuild_index()
        logger.info("FAISS add tenant=%s total=%d", self.tenant_id, len(self._metadata))

    def search(self, query_embedding: list[float], top_k: int, threshold: float) -> list[dict]:
        self._load()
        if self._index is None or self._index.ntotal == 0:
            return []
        q = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(q)
        k = min(top_k, self._index.ntotal)
        scores, indices = self._index.search(q, k)
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or score < threshold:
                continue
            meta = {k: v for k, v in self._metadata[idx].items() if k != "_vector"}
            meta["score"] = float(score)
            meta["text"] = meta.get("text", "")
            results.append(meta)
        return results

    def remove_by_doc_id(self, doc_id: str) -> int:
        self._load()
        before = len(self._metadata)
        self._metadata = [m for m in self._metadata if m.get("doc_id") != doc_id]
        removed = before - len(self._metadata)
        if removed:
            self._rebuild_index()
            logger.info("FAISS removed doc_id=%s count=%d", doc_id, removed)
        return removed
