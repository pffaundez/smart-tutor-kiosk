import json
import random
import re
import time
from dataclasses import dataclass, asdict
from typing import Any

import requests
from datasets import load_dataset


OLLAMA_BASE_URL = "http://127.0.0.1:11434"
MODELS = [
    "qwen3:0.6b",
    "qwen2.5:3b",
    "qwen2.5:7b",
]
SAMPLE_SIZE = 100
SEED = 42
DATASET_NAME = "cais/mmlu"
DATASET_SPLIT = "test"


@dataclass
class QuestionResult:
    question_id: int
    subject: str
    question: str
    choices: list[str]
    gold_index: int
    pred_index: int | None
    correct: bool
    latency_s: float
    raw_response: str


@dataclass
class ModelSummary:
    model: str
    total_questions: int
    answered_questions: int
    correct: int
    accuracy: float
    avg_latency_s: float
    total_time_s: float


def fetch_ollama_models(base_url: str) -> list[str]:
    """Return installed model names from Ollama."""
    resp = requests.get(f"{base_url}/api/tags", timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return [m["name"] for m in data.get("models", [])]


def ensure_models_available(base_url: str, models: list[str]) -> None:
    installed = set(fetch_ollama_models(base_url))
    missing = [m for m in models if m not in installed]
    if missing:
        raise RuntimeError(
            "These models are not installed in Ollama: "
            + ", ".join(missing)
            + "\nRun e.g. `ollama pull <model>` first."
        )


def load_mmlu_sample(sample_size: int, seed: int) -> list[dict[str, Any]]:
    """
    Load MMLU and sample questions.

    This script expects rows with:
      - question
      - choices
      - answer
      - subject
    """
    ds = load_dataset(DATASET_NAME, "all", split=DATASET_SPLIT)

    rng = random.Random(seed)
    indices = list(range(len(ds)))
    rng.shuffle(indices)
    selected = indices[:sample_size]

    rows: list[dict[str, Any]] = []
    for i in selected:
        row = ds[i]

        # Normalize field names defensively.
        question = row.get("question") or row.get("input")
        choices = row.get("choices") or row.get("options")
        answer = row.get("answer") or row.get("target")
        subject = row.get("subject") or row.get("task") or "unknown"

        if question is None or choices is None or answer is None:
            raise ValueError(f"Unexpected dataset row format: {row}")

        rows.append(
            {
                "question_id": i,
                "subject": subject,
                "question": question,
                "choices": list(choices),
                "answer": int(answer),
            }
        )

    return rows


def build_prompt(question: str, choices: list[str]) -> str:
    letters = ["A", "B", "C", "D", "E", "F"]
    rendered_choices = "\n".join(
        f"{letters[i]}. {choice}" for i, choice in enumerate(choices)
    )
    return f"""You are answering a multiple-choice benchmark question.

Return ONLY one capital letter: A, B, C, D, E, or F.
Do not explain your reasoning.
Do not output any other text.

Question:
{question}

Choices:
{rendered_choices}

Answer:"""


def ask_ollama(base_url: str, model: str, prompt: str) -> tuple[str, float]:
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
        "stream": False,
        "options": {
            "temperature": 0,
        },
    }

    start = time.perf_counter()
    resp = requests.post(f"{base_url}/api/chat", json=payload, timeout=180)
    latency = time.perf_counter() - start
    resp.raise_for_status()

    data = resp.json()
    text = data["message"]["content"].strip()
    return text, latency


def parse_letter_answer(text: str, num_choices: int) -> int | None:
    """
    Extract A-F from the model response.
    Returns the choice index or None.
    """
    letters = ["A", "B", "C", "D", "E", "F"][:num_choices]

    # Strict single-letter fast path.
    cleaned = text.strip().upper()
    if cleaned in letters:
        return letters.index(cleaned)

    # Try to find first standalone capital letter.
    match = re.search(r"\b([A-F])\b", cleaned)
    if match:
        letter = match.group(1)
        if letter in letters:
            return letters.index(letter)

    return None


def run_model_benchmark(
    base_url: str,
    model: str,
    questions: list[dict[str, Any]],
) -> tuple[ModelSummary, list[QuestionResult]]:
    results: list[QuestionResult] = []
    start_total = time.perf_counter()

    for row in questions:
        prompt = build_prompt(row["question"], row["choices"])
        raw_response, latency_s = ask_ollama(base_url, model, prompt)
        pred_index = parse_letter_answer(raw_response, len(row["choices"]))
        correct = pred_index == row["answer"]

        results.append(
            QuestionResult(
                question_id=row["question_id"],
                subject=row["subject"],
                question=row["question"],
                choices=row["choices"],
                gold_index=row["answer"],
                pred_index=pred_index,
                correct=correct,
                latency_s=latency_s,
                raw_response=raw_response,
            )
        )

    total_time_s = time.perf_counter() - start_total
    answered = sum(r.pred_index is not None for r in results)
    correct = sum(r.correct for r in results)
    avg_latency = sum(r.latency_s for r in results) / len(results)

    summary = ModelSummary(
        model=model,
        total_questions=len(results),
        answered_questions=answered,
        correct=correct,
        accuracy=correct / len(results),
        avg_latency_s=avg_latency,
        total_time_s=total_time_s,
    )
    return summary, results


def save_results(
    out_path: str,
    summaries: list[ModelSummary],
    detailed: dict[str, list[QuestionResult]],
) -> None:
    payload = {
        "summaries": [asdict(s) for s in summaries],
        "details": {
            model: [asdict(r) for r in rows]
            for model, rows in detailed.items()
        },
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def print_summary_table(summaries: list[ModelSummary]) -> None:
    print("\n=== Benchmark Summary ===")
    print(
        f"{'Model':20} {'Acc':>8} {'Correct':>10} {'Answered':>10} "
        f"{'Avg Lat(s)':>12} {'Total(s)':>10}"
    )
    print("-" * 80)
    for s in summaries:
        print(
            f"{s.model:20} "
            f"{s.accuracy:8.2%} "
            f"{s.correct:10d} "
            f"{s.answered_questions:10d} "
            f"{s.avg_latency_s:12.2f} "
            f"{s.total_time_s:10.2f}"
        )


def main() -> None:
    print("Checking Ollama models...")
    ensure_models_available(OLLAMA_BASE_URL, MODELS)

    print(f"Loading {SAMPLE_SIZE} MMLU questions...")
    questions = load_mmlu_sample(SAMPLE_SIZE, SEED)

    summaries: list[ModelSummary] = []
    detailed: dict[str, list[QuestionResult]] = {}

    for model in MODELS:
        print(f"\nRunning benchmark for {model} ...")
        summary, rows = run_model_benchmark(OLLAMA_BASE_URL, model, questions)
        summaries.append(summary)
        detailed[model] = rows
        print(
            f"Done: accuracy={summary.accuracy:.2%}, "
            f"avg_latency={summary.avg_latency_s:.2f}s"
        )

    print_summary_table(summaries)
    save_results("benchmark_results_qwen.json", summaries, detailed)
    print("\nSaved detailed results to benchmark_results_qwen.json")


if __name__ == "__main__":
    main()