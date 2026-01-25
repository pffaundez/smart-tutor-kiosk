from __future__ import annotations
import re
from dataclasses import dataclass

@dataclass
class Chunk:
    topic_id: str
    chunk_id: str
    text: str

def split_sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text.strip())
    if not text:
        return []
    return re.split(r"(?<=[.!?])\s+", text)

def make_chunks(topic_id: str, source_text: str, sentences_per_chunk: int = 3, overlap: int = 1) -> list[Chunk]:
    sents = split_sentences(source_text)
    if not sents:
        return []

    chunks: list[Chunk] = []
    i = 0
    c = 0
    while i < len(sents):
        window = sents[i : i + sentences_per_chunk]
        chunk_text = " ".join(window).strip()
        if chunk_text:
            chunks.append(Chunk(topic_id=topic_id, chunk_id=f"{topic_id}_c{c:03d}", text=chunk_text))
            c += 1
        i += max(1, sentences_per_chunk - overlap)

    return chunks
