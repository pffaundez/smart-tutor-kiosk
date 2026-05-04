from app.core.text_processor import format_easy_to_read
from app.prompts.reexplain_modes import (
    get_sys_prompt,
    build_custom_domain_prompt,
)


def _looks_truncated(text: str) -> bool:
    text = text.strip()
    if not text:
        return True

    # Heurística simple:
    # si no termina en puntuación fuerte, puede haber quedado cortado.
    return not text.endswith((".", "!", "?", '"', "”"))


def generate_reexplanation(
    client,
    topic_lesson: str,
    selected_key: str,
    custom_domain: str | None = None,
):
    if selected_key == "custom_domain_analogies":
        if not custom_domain:
            raise ValueError("A custom domain is required for custom_domain_analogies.")
        sys_prompt = build_custom_domain_prompt(custom_domain)
    else:
        sys_prompt = get_sys_prompt(selected_key)

    user_prompt = (
        "Rewrite the following LESSON according to the system instructions.\n\n"
        f"LESSON:\n<<<\n{topic_lesson}\n>>>\n"
    )

    max_tokens_by_mode = {
        "easy_to_read": 260,
        "simple": 220,
        "daily_analogies": 280,
        "custom_domain_analogies": 300,
    }

    max_tokens = max_tokens_by_mode.get(selected_key, 260)

    out = client.chat(
        sys_prompt,
        user_prompt,
        max_tokens=max_tokens,
        temperature=0.0,
    )
    text = out["text"].strip()

    # Reintento simple si parece truncado
    if _looks_truncated(text):
        retry_out = client.chat(
            sys_prompt,
            user_prompt,
            max_tokens=max_tokens + 120,
            temperature=0.0,
        )
        retry_text = retry_out["text"].strip()

        if len(retry_text) > len(text):
            text = retry_text
            out = retry_out

    if selected_key == "easy_to_read":
        text = format_easy_to_read(text)

    return text, out["latency_ms"]