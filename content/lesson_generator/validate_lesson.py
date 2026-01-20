from __future__ import annotations

import argparse
import re
from pathlib import Path


def word_count(text: str) -> int:
    # Count words (letters/numbers/apostrophes inside words)
    words = re.findall(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)?", text)
    return len(words)


def split_paragraphs(text: str) -> list[str]:
    # Paragraphs separated by one or more blank lines
    paras = [p.strip() for p in re.split(r"\n\s*\n+", text.strip()) if p.strip()]
    return paras


def has_bullets(text: str) -> bool:
    # Simple bullet/list detection for markdown-like lists
    bullet_re = re.compile(r"^\s*(?:[-*•]|(\d+)[\.\)])\s+", re.MULTILINE)
    return bool(bullet_re.search(text))


def has_questions(text: str) -> bool:
    return "?" in text


def has_headings(text: str) -> bool:
    # Markdown headings
    return bool(re.search(r"^\s*#{1,6}\s+\S+", text, re.MULTILINE))


def novelty_ratio(source: str, lesson: str) -> float:
    """
    Heuristic: ratio of unique content-words in lesson that do NOT appear in source.
    Not perfect, but helps catch "new facts" creeping in.
    """
    def norm_words(t: str) -> set[str]:
        words = re.findall(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)?", t.lower())
        # remove very short tokens to reduce noise
        return {w for w in words if len(w) >= 4}

    src = norm_words(source)
    les = norm_words(lesson)
    if not les:
        return 1.0
    novel = {w for w in les if w not in src}
    return len(novel) / max(1, len(les))


def validate(
    lesson_text: str,
    source_text: str | None,
    min_words: int,
    max_words: int,
    min_paras: int,
    max_paras: int,
    max_novelty_ratio: float | None,
) -> list[str]:
    errors: list[str] = []

    wc = word_count(lesson_text)
    if wc < min_words or wc > max_words:
        errors.append(f"Word count out of range: {wc} (expected {min_words}-{max_words}).")

    paras = split_paragraphs(lesson_text)
    if len(paras) < min_paras or len(paras) > max_paras:
        errors.append(f"Paragraph count out of range: {len(paras)} (expected {min_paras}-{max_paras}).")

    if has_questions(lesson_text):
        errors.append("Lesson contains a question mark '?'. Questions are not allowed.")

    if has_bullets(lesson_text):
        errors.append("Lesson appears to contain bullet points or numbered lists. Lists are not allowed.")

    if has_headings(lesson_text):
        errors.append("Lesson contains markdown headings (e.g., '# Title'). Headings are not allowed.")

    if max_novelty_ratio is not None and source_text is not None:
        ratio = novelty_ratio(source_text, lesson_text)
        if ratio > max_novelty_ratio:
            errors.append(
                f"Novelty ratio too high: {ratio:.2f} (max {max_novelty_ratio}). "
                "This may indicate the model introduced terms not present in the source."
            )

    return errors


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate generated lesson.md constraints.")
    ap.add_argument("--lesson", required=True, help="Path to lesson markdown (draft or final).")
    ap.add_argument("--source", required=False, help="Path to source.md (optional but recommended).")
    ap.add_argument("--min-words", type=int, default=100)
    ap.add_argument("--max-words", type=int, default=150)
    ap.add_argument("--min-paras", type=int, default=2)
    ap.add_argument("--max-paras", type=int, default=3)
    ap.add_argument("--max-novelty-ratio", type=float, default=0.30,
                    help="Heuristic threshold; set to 1.0 to disable effectively.")
    args = ap.parse_args()

    lesson_path = Path(args.lesson)
    if not lesson_path.exists():
        print(f"ERROR: lesson file not found: {lesson_path}")
        return 2

    lesson_text = lesson_path.read_text(encoding="utf-8")

    source_text = None
    if args.source:
        source_path = Path(args.source)
        if not source_path.exists():
            print(f"ERROR: source file not found: {source_path}")
            return 2
        source_text = source_path.read_text(encoding="utf-8")

    errors = validate(
        lesson_text=lesson_text,
        source_text=source_text,
        min_words=args.min_words,
        max_words=args.max_words,
        min_paras=args.min_paras,
        max_paras=args.max_paras,
        max_novelty_ratio=args.max_novelty_ratio if args.max_novelty_ratio < 1.0 else None,
    )

    if errors:
        print("VALIDATION FAILED:")
        for e in errors:
            print(f"- {e}")
        return 1

    print("VALIDATION OK ✅")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
