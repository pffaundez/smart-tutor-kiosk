from pathlib import Path
import streamlit as st

from app.llm.client import LLMClient

st.set_page_config(page_title="Inference Smoke Test", layout="centered")

st.title("Inference Smoke Test (Local with Ollama)")
st.caption("Loads an existing lesson.md and runs LLM calls to validate the inference interface.")

# --- Ollama configuration ---
base_url = st.text_input("Ollama base URL", value="http://127.0.0.1:11434")
model_name = st.text_input("Model name", value="tinyllama")

lesson_path = st.text_input("Lesson file path", value="content/topics/topic001/lesson.md")

# --- Load lesson ---
try:
    lesson_text = Path(lesson_path).read_text(encoding="utf-8").strip()
except Exception as e:
    st.error(f"Could not read lesson file: {e}")
    st.stop()

st.subheader("Loaded lesson.md")
st.text_area("Lesson text", value=lesson_text, height=220)

st.divider()

# --- Inference settings ---
col1, col2 = st.columns(2)
with col1:
    max_tokens = st.slider("max_tokens (num_predict)", 64, 512, 220, step=16)
with col2:
    temperature = st.slider("temperature", 0.0, 1.0, 0.2, step=0.1)

client = LLMClient(base_url=base_url, model=model_name)

# --- Test 1: Rephrase ---
st.subheader("Test 1: Rephrase (same meaning)")
sys_prompt_1 = st.text_area(
    "System prompt (Test 1)",
    value="You are a concise educational assistant. Follow instructions strictly.",
    height=70,
)
user_prompt_1 = st.text_area(
    "User prompt (Test 1)",
    value=(
        "Rephrase the lesson below in simpler English without adding new facts. "
        "Keep it under 120 words and use 2 short paragraphs.\n\n"
        f"LESSON:\n{lesson_text}"
    ),
    height=170,
)

if st.button("Run Test 1"):
    try:
        with st.spinner("Calling Ollama..."):
            result = client.chat(
                system_prompt=sys_prompt_1,
                user_prompt=user_prompt_1,
                max_tokens=max_tokens,
                temperature=temperature,
            )
        st.success(f"OK ✅ | {result['latency_ms']:.0f} ms")
        st.text_area("LLM output (Test 1)", value=result["text"], height=220)
    except Exception as e:
        st.error(f"FAILED ❌ {e}")

st.divider()

# --- Test 2: Generate 4 questions (draft) ---
st.subheader("Test 2: Draft 4 multiple-choice questions")
sys_prompt_2 = st.text_area(
    "System prompt (Test 2)",
    value="You write clear multiple-choice questions. Do not add facts not present in the lesson.",
    height=70,
)
user_prompt_2 = st.text_area(
    "User prompt (Test 2)",
    value=(
        "Write 4 multiple-choice questions about the lesson below. "
        "Each question must have 4 options (A-D) and mark the correct option.\n\n"
        f"LESSON:\n{lesson_text}"
    ),
    height=170,
)

if st.button("Run Test 2"):
    try:
        with st.spinner("Calling Ollama..."):
            result = client.chat(
                system_prompt=sys_prompt_2,
                user_prompt=user_prompt_2,
                max_tokens=max_tokens,
                temperature=temperature,
            )
        st.success(f"OK ✅ | {result['latency_ms']:.0f} ms")
        st.text_area("LLM output (Test 2)", value=result["text"], height=260)
    except Exception as e:
        st.error(f"FAILED ❌ {e}")

