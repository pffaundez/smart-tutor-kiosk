from __future__ import annotations
import json
from pathlib import Path
from typing import Any

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

INDEX_DIR = Path("content/index")
CHUNKS_PATH = INDEX_DIR / "chunks.jsonl"
FAISS_PATH = INDEX_DIR / "faiss.index"
META_PATH = INDEX_DIR / "meta.json"

class EmbeddingRetriever:
    def __init__(self):
        meta = json.loads(META_PATH.read_text(encoding="utf-8"))
        self.model_name = meta["embedding_model"]
        self.model = SentenceTransformer(self.model_name)
        self.index = faiss.read_index(str(FAISS_PATH))

        self.chunks: list[dict[str, Any]] = []
        for line in CHUNKS_PATH.read_text(encoding="utf-8").splitlines():
            self.chunks.append(json.loads(line))

    def retrieve(self, query: str, topic_id: str | None = None, k: int = 6) -> list[dict]:
        q = self.model.encode([query], normalize_embeddings=True)
        q = np.asarray(q, dtype=np.float32)

        scores, idxs = self.index.search(q, k * 3)
        scores = scores[0].tolist()
        idxs = idxs[0].tolist()

        results = []
        for score, idx in zip(scores, idxs):
            if idx < 0 or idx >= len(self.chunks):
                continue
            ch = self.chunks[idx]
            if topic_id is not None and ch["topic_id"] != topic_id:
                continue
            results.append({**ch, "score": float(score)})
            if len(results) >= k:
                break

        return results
