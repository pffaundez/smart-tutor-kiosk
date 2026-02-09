from __future__ import annotations
import json
import time
from pathlib import Path
from typing import Any

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from collections import OrderedDict

INDEX_DIR = Path("content/index")
CHUNKS_PATH = INDEX_DIR / "chunks.jsonl"
FAISS_PATH = INDEX_DIR / "faiss.index"
META_PATH = INDEX_DIR / "meta.json"

class EmbeddingRetriever:

    def __init__(self, embed_cache_max: int = 1000):
        meta = json.loads(META_PATH.read_text(encoding="utf-8"))
        self.model_name = meta["embedding_model"]
        self.model = SentenceTransformer(self.model_name)
        self.index = faiss.read_index(str(FAISS_PATH))

        self.chunks: list[dict[str, Any]] = []
        for line in CHUNKS_PATH.read_text(encoding="utf-8").splitlines():
            self.chunks.append(json.loads(line))

        # In-memory LRU cache for query embeddings (maps normalized_query -> np.ndarray)
        self._embed_cache: OrderedDict[str, np.ndarray] = OrderedDict()
        self._embed_cache_max = embed_cache_max

    
    def retrieve(self, query: str, topic_id: str | None = None, k: int = 6) -> list[dict]:
        q = self._get_embeddings_for_queries([query])
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


    def retrieve_batch(self, queries: list[str], topic_id: str | None = None, k: int = 6) -> list[list[dict]]:
        """
        Retrieve results for multiple queries in batch.
        Returns a list (same order as `queries`) of lists of up to `k` result dicts.
        Uses the cached/batched embedding helper to avoid repeated model.encode calls.
        """
        if not queries:
            return [[] for _ in queries]

        # Get (cached or newly computed) embeddings for all queries in one call.
        # This reuses cached embeddings and only encodes the missing items in batch.
        t0 = time.perf_counter()
        q_embeddings = self._get_embeddings_for_queries(queries)  # shape: (len(queries), dim)
        t_encode = (time.perf_counter() - t0) * 1000
        
        if q_embeddings.size == 0:
            return [[] for _ in queries]

        # Use FAISS to search all embeddings at once
        t0 = time.perf_counter()
        scores, idxs = self.index.search(q_embeddings, k * 3)  # shape: (len(queries), k*3)
        t_search = (time.perf_counter() - t0) * 1000
        
        # Log timing info
        cache_size = len(self._embed_cache)
        print(f"[retriever] encode_ms={t_encode:.1f} search_ms={t_search:.1f} queries={len(queries)} cache_size={cache_size}")

        results_batch: list[list[dict]] = []
        for row_scores, row_idxs in zip(scores.tolist(), idxs.tolist()):
            row_results: list[dict] = []
            for score, idx in zip(row_scores, row_idxs):
                if idx < 0 or idx >= len(self.chunks):
                    continue
                ch = self.chunks[idx]
                if topic_id is not None and ch.get("topic_id") != topic_id:
                    continue
                row_results.append({**ch, "score": float(score)})
                if len(row_results) >= k:
                    break
            results_batch.append(row_results)

        return results_batch
    

    def _normalize_query(self, query: str) -> str:
        return query.strip().lower()

    def _get_embeddings_for_queries(self, queries: list[str]) -> np.ndarray:
        """
        Return embeddings for queries in the same order.
        Reuse cached embeddings when available; compute embeddings in batch for misses.
        """
        if not queries:
            return np.zeros((0, self.model.get_sentence_embedding_dimension()), dtype=np.float32)

        # Map normalized -> original indices
        normalized = [self._normalize_query(q) for q in queries]

        # Determine which normalized queries we need to compute
        missing = []
        missing_idx = []
        embeddings = [None] * len(queries)

        for i, nq in enumerate(normalized):
            if nq in self._embed_cache:
                embeddings[i] = self._embed_cache[nq]
                # move to end (recently used)
                self._embed_cache.move_to_end(nq)
            else:
                missing.append(queries[i])
                missing_idx.append(i)

        # Compute embeddings for missing queries in one batch
        if missing:
            computed = self.model.encode(missing, normalize_embeddings=True)
            computed = np.asarray(computed, dtype=np.float32)
            # Store computed embeddings into results and cache
            ci = 0
            for idx in missing_idx:
                emb = computed[ci]
                embeddings[idx] = emb
                nq = normalized[idx]
                # add to cache and evict oldest if needed
                self._embed_cache[nq] = emb
                self._embed_cache.move_to_end(nq)
                ci += 1

            # Evict if cache too big
            while len(self._embed_cache) > self._embed_cache_max:
                self._embed_cache.popitem(last=False)

        # Stack into numpy array (num_queries, dim)
        stacked = np.vstack([e for e in embeddings])
        return stacked
