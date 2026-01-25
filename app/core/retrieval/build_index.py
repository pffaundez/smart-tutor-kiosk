from __future__ import annotations
import json
from pathlib import Path

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

from app.core.retrieval.chunker import make_chunks

TOPICS_DIR = Path("content/topics")
INDEX_DIR = Path("content/index")
CHUNKS_PATH = INDEX_DIR / "chunks.jsonl"
FAISS_PATH = INDEX_DIR / "faiss.index"
META_PATH = INDEX_DIR / "meta.json"

EMBED_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"  # CPU-friendly

def main():
    INDEX_DIR.mkdir(parents=True, exist_ok=True)

    topic_dirs = [p for p in TOPICS_DIR.iterdir() if p.is_dir()]
    all_chunks = []

    for td in sorted(topic_dirs, key=lambda x: x.name):
        source_path = td / "source.md"
        if not source_path.exists():
            continue
        source = source_path.read_text(encoding="utf-8").strip()
        chunks = make_chunks(td.name, source_text=source, sentences_per_chunk=3, overlap=1)
        all_chunks.extend(chunks)

    if not all_chunks:
        raise RuntimeError("No chunks produced. Check content/topics/*/source.md")

    with CHUNKS_PATH.open("w", encoding="utf-8") as f:
        for ch in all_chunks:
            f.write(json.dumps({
                "topic_id": ch.topic_id,
                "chunk_id": ch.chunk_id,
                "text": ch.text
            }, ensure_ascii=False) + "\n")

    model = SentenceTransformer(EMBED_MODEL_NAME)
    texts = [ch.text for ch in all_chunks]
    embs = model.encode(texts, normalize_embeddings=True, show_progress_bar=True)
    embs = np.asarray(embs, dtype=np.float32)

    dim = embs.shape[1]
    index = faiss.IndexFlatIP(dim)  # cosine via inner product on normalized vectors
    index.add(embs)
    faiss.write_index(index, str(FAISS_PATH))

    META_PATH.write_text(json.dumps({
        "embedding_model": EMBED_MODEL_NAME,
        "num_chunks": len(all_chunks),
        "dim": dim
    }, indent=2), encoding="utf-8")

    print(f"OK ✅ Built index with {len(all_chunks)} chunks")

if __name__ == "__main__":
    main()
