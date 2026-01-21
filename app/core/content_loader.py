import json
from pathlib import Path


TOPICS_DIR = Path("content/topics")


def list_topics():
    if not TOPICS_DIR.exists():
        return []
    topics = []
    for p in sorted(TOPICS_DIR.iterdir()):
        if p.is_dir():
            topics.append(p.name)
    return topics


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_topic(topic_id: str) -> dict:
    topic_dir = TOPICS_DIR / topic_id
    lesson_path = topic_dir / "lesson.md"
    source_path = topic_dir / "source.md"
    quiz1_path = topic_dir / "quiz_1.json"
    quiz2_path = topic_dir / "quiz_2.json"

    data = {
        "id": topic_id,
        "lesson": load_text(lesson_path) if lesson_path.exists() else "",
        "source": load_text(source_path) if source_path.exists() else "",
        "quiz_1": load_json(quiz1_path) if quiz1_path.exists() else None,
        "quiz_2": load_json(quiz2_path) if quiz2_path.exists() else None,
    }
    return data
