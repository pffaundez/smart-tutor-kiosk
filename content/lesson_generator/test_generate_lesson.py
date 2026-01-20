from pathlib import Path
import subprocess

from app.llm.client import LLMClient

TOPIC_ID = "nn_basics"

PROMPT_PATH = Path("content/lesson_generation/generate_lesson.txt")
SOURCE_PATH = Path(f"content/topics/{TOPIC_ID}/source.md")

DRAFT_PATH = Path(f"content/topics/{TOPIC_ID}/lesson.draft.md")
FINAL_PATH = Path(f"content/topics/{TOPIC_ID}/lesson.md")

VALIDATOR_PATH = Path("content/lesson_generation/validate_lesson.py")


def main():
    prompt_template = PROMPT_PATH.read_text(encoding="utf-8")
    source_text = SOURCE_PATH.read_text(encoding="utf-8")

    user_prompt = prompt_template.replace("{SOURCE_TEXT}", source_text)

    client = LLMClient("http://127.0.0.1:8080/v1/chat/completions")

    result = client.chat(
        system_prompt="You are a precise educational editor. Follow constraints strictly.",
        user_prompt=user_prompt,
        max_tokens=220,
        temperature=0.1
    )

    text = result["text"].strip()
    DRAFT_PATH.write_text(text + "\n", encoding="utf-8")

    print(f"Draft written to: {DRAFT_PATH}")
    print(f"Latency: {round(result['latency_ms'], 1)} ms")

    # Validate draft (using the topic source for the novelty heuristic)
    cmd = [
        "python",
        str(VALIDATOR_PATH),
        "--lesson", str(DRAFT_PATH),
        "--source", str(SOURCE_PATH),
        "--min-words", "100",
        "--max-words", "150",
        "--min-paras", "2",
        "--max-paras", "3",
        "--max-novelty-ratio", "0.30",
    ]
    completed = subprocess.run(cmd, capture_output=True, text=True)
    print(completed.stdout.strip())
    if completed.returncode != 0:
        print(completed.stderr.strip())
        raise SystemExit(completed.returncode)

    # Promote to final if validation OK
    FINAL_PATH.write_text(text + "\n", encoding="utf-8")
    print(f"Promoted to final: {FINAL_PATH} ✅")


if __name__ == "__main__":
    main()
