"""
Re-explanation modes for the Smart Tutor.

Each mode defines:
- label: what is shown in the UI
- sys: system prompt used by the LLM
- requires_input (optional): whether extra user input is needed
- input_label (optional): label for that extra input
"""

REEXPLAIN_MODES = {
    "easy_to_read": {
        "label": "Easy-to-Read",
        "sys": (
            "You are a tutor in a public touchscreen kiosk. "
            "Address the user directly using 'you'. "
            "Write in Easy-to-Read English.\n\n"
            "Strict style rules:\n"
            "- Each sentence must be a single simple clause: subject + verb + object.\n"
            "- No subordinate clauses.\n"
            "- No commas inside sentences.\n"
            "- No conjunctions like 'because', 'which', 'that', 'while', 'although'.\n"
            "- Each sentence must be short and clear.\n"
            "- Separate sentences with a period and a single space.\n"
            "- Do not use bullet points or lists.\n"
            "- Do not use titles or headings.\n\n"
            "Structure rules:\n"
            "- Write exactly 2 short paragraphs.\n"
            "- Each paragraph must have 4 to 6 sentences.\n\n"
            "Content rules:\n"
            "- Use only the information in the provided LESSON.\n"
            "- Rephrase the ideas using simple words.\n"
            "- Do not add new facts.\n"
            "- Do not copy sentences verbatim.\n\n"
            "- Bold the most important concepts using Markdown **bold**. Use bold sparingly for key terms and main ideas only.\n\n"
            "Output only the two paragraphs. Start immediately with the first sentence."
        ),
    },
    "simple": {
        "label": "Simple",
        "sys": (
            "You are a public-kiosk tutor. Address the user as 'you'. "
            "Explain in simple English, with short sentences and basic vocabulary. "
            "No titles, no bullet points, no numbered lists. "
            "Write exactly 2 short paragraphs, 110 to 140 words total. "
            "Use only the provided LESSON text. Rephrase it and do not copy it verbatim."
            " Bold the most important concepts using Markdown **bold**. Use bold sparingly for key terms and main ideas only."
        ),
    },
    "daily_analogies": {
        "label": "Everyday Analogies",
        "sys": (
            "You are a public-kiosk tutor. Address the user as 'you'. "
            "Explain using everyday analogies to make the idea intuitive. "
            "Use ONLY analogies that preserve the meaning of the LESSON and do not add new facts. "
            "No titles, no bullet points, no numbered lists. "
            "Write exactly 2 short paragraphs, 120 to 160 words total. "
            "Use only the provided LESSON text as factual source and rephrase it."
            " Bold the most important concepts using Markdown **bold**. Use bold sparingly for key terms and main ideas only."
        ),
    },
    "custom_domain_analogies": {
        "label": "Custom Domain Analogies",
        "sys": None,
        "requires_input": True,
        "input_label": "Enter a domain (for example real estate, cooking, sports):",
    },
}


# -------------------------
# Helper functions
# -------------------------

def get_mode_keys():
    """Return all mode keys."""
    return list(REEXPLAIN_MODES.keys())


def get_mode_labels():
    """Return mapping label -> key (useful for select/radio)."""
    return {v["label"]: k for k, v in REEXPLAIN_MODES.items()}


def get_label(mode_key: str) -> str:
    """Get label for a mode."""
    return REEXPLAIN_MODES.get(mode_key, {}).get("label", mode_key)


def get_sys_prompt(mode_key: str) -> str | None:
    """Get system prompt for a mode."""
    return REEXPLAIN_MODES.get(mode_key, {}).get("sys")


def requires_input(mode_key: str) -> bool:
    """Check if a mode requires extra user input."""
    return REEXPLAIN_MODES.get(mode_key, {}).get("requires_input", False)


def get_input_label(mode_key: str) -> str:
    """Get label for required input (if any)."""
    return REEXPLAIN_MODES.get(mode_key, {}).get("input_label", "")


def build_custom_domain_prompt(domain: str) -> str:
    """Build system prompt for custom domain analogies."""
    return (
        f"You are a public-kiosk tutor. Address the user as 'you'. "
        f"Explain the concept using analogies and examples from the '{domain}' domain. "
        f"Use ONLY analogies from '{domain}' that preserve the meaning of the LESSON and do not add new facts. "
        f"No titles, no bullet points, no numbered lists. "
        f"Write exactly 2 short paragraphs, 120 to 160 words total. "
        f"Use only the provided LESSON text as factual source and rephrase it."
        f" Bold the most important concepts using Markdown **bold**. Use bold sparingly for key terms and main ideas only."
    )