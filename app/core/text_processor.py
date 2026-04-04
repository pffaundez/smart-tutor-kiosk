import re
from html import escape

def split_long_sentences(text: str) -> str:
    """
    Split sentences that contain multiple actions into smaller ones.
    """
    # Separar patrones comunes de múltiples acciones
    text = re.sub(r",\s+then\s+", ". Then ", text)
    text = re.sub(r"\s+then\s+", ". Then ", text)
    text = re.sub(r",\s+and\s+", ". And ", text)
    text = re.sub(r"\s+and\s+", ". And ", text)

    # Evitar duplicación de puntos
    text = re.sub(r"\.\s*\.", ".", text)

    return text


def clean_sentences(sentences: list[str]) -> list[str]:
    """
    Clean and normalize sentences.
    """
    cleaned = []

    for s in sentences:
        s = s.strip()

        # Capitalizar primera letra si hace falta
        if s and not s[0].isupper():
            s = s[0].upper() + s[1:]

        cleaned.append(s)

    return cleaned


def format_easy_to_read(text: str) -> str:
    """
    Process the generated text for easy_to_read mode.

    Improvements:
    - Splits long sentences into smaller ones
    - Ensures one idea per line
    - Adds spacing for readability
    """

    # 🔥 Paso 1: romper oraciones largas
    text = split_long_sentences(text)

    # 🔹 Paso 2: separar en oraciones
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())

    # 🔹 Paso 3: limpiar
    sentences = [s for s in sentences if s.strip()]
    sentences = clean_sentences(sentences)

    # 🔥 Paso 4: forzar máximo 1 idea por línea
    # (opcional: si una oración sigue siendo muy larga)
    final_sentences = []
    for s in sentences:
        if len(s.split()) > 18:
            parts = re.split(r",\s+", s)
            final_sentences.extend(parts)
        else:
            final_sentences.append(s)

    # 🔹 Paso 5: formatear output
    formatted_text = '\n\n'.join(final_sentences)

    return formatted_text



def _bionicize_word(word: str) -> str:
    """
    Wrap the first part of a word in <strong>...</strong>.
    Keeps punctuation around the word.
    """
    match = re.match(r"^([^A-Za-z0-9]*)([A-Za-z0-9'-]+)([^A-Za-z0-9]*)$", word)
    if not match:
        return escape(word)

    prefix, core, suffix = match.groups()

    if len(core) <= 2:
        split_idx = 1
    elif len(core) <= 4:
        split_idx = 2
    elif len(core) <= 7:
        split_idx = 3
    else:
        split_idx = max(3, len(core) // 2)

    first = escape(core[:split_idx])
    rest = escape(core[split_idx:])

    return f"{escape(prefix)}<strong>{first}</strong>{rest}{escape(suffix)}"


def bionic_reading_html(markdown_text: str) -> str:
    """
    Convert plain markdown-ish lesson text into simple HTML paragraphs
    with bionic-reading emphasis on each word.

    Notes:
    - Keeps paragraph breaks
    - Keeps bullet-like lines starting with '-', '*'
    - Does not try to fully parse markdown
    """
    paragraphs = [p.strip() for p in markdown_text.strip().split("\n\n") if p.strip()]
    html_parts = []

    for para in paragraphs:
        lines = [line.strip() for line in para.split("\n") if line.strip()]

        # Simple bullet list support
        if lines and all(line.startswith(("-", "*")) for line in lines):
            items = []
            for line in lines:
                content = line[1:].strip()
                words = content.split()
                bionic = " ".join(_bionicize_word(w) for w in words)
                items.append(f"<li>{bionic}</li>")
            html_parts.append(f"<ul>{''.join(items)}</ul>")
            continue

        words = para.split()
        bionic = " ".join(_bionicize_word(w) for w in words)
        html_parts.append(f"<p>{bionic}</p>")

    return "\n".join(html_parts)