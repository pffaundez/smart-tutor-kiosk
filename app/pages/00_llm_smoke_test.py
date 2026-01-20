import streamlit as st
from app.llm.client import LLMClient

st.set_page_config(page_title="LLM Smoke Test ", layout="centered")

st.title("LLM Smoke Test (Ollama)")
st.caption("Direct LLM test using Ollama /api/chat. No lesson loading, just raw prompts.")

base_url = st.text_input("Ollama base URL", value="http://127.0.0.1:11434")
model_name = st.text_input("Model name", value="tinyllama:latest")

system_prompt = st.text_area(
    "System prompt",
    value="You are a concise assistant. Follow the user's constraints strictly.",
    height=90,
)
user_prompt = st.text_area(
    "User prompt",
    value="Say hello in one short sentence.",
    height=120,
)

col1, col2 = st.columns(2)
with col1:
    max_tokens = st.slider("max_tokens (num_predict)", 16, 256, 64, step=16)
with col2:
    temperature = st.slider("temperature", 0.0, 1.0, 0.2, step=0.1)

client = LLMClient(base_url=base_url, model=model_name)

if st.button("Run inference"):
    try:
        with st.spinner("Calling Ollama..."):
            result = client.chat(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
            )
        st.success(f"OK ✅ | {result['latency_ms']:.0f} ms")
        st.text_area("Output", value=result["text"], height=220)
    except Exception as e:
        st.error(f"FAILED ❌ {e}")
        st.info("Check: Ollama running (`ollama serve`) and model name matches `ollama list`.")

