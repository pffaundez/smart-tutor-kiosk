import time
import requests
import streamlit as st

from app.llm.client import LLMClient

st.set_page_config(page_title="Compatibility Test ", layout="centered")

st.title("Compatibility Test")
st.caption("Basic kiosk checks: UI/touch + network + Ollama inference (local).")

# ----------------------------
# 1) UI / Touch sanity
# ----------------------------
st.subheader("1) UI / Touch sanity")
c1, c2, c3 = st.columns(3)
with c1:
    if st.button("Tap Test"):
        st.success("Tap registered ✅")
with c2:
    st.checkbox("Checkbox Test")
with c3:
    st.radio("Radio Test", options=["Option A", "Option B", "Option C"], horizontal=True)

st.divider()

# ----------------------------
# 2) Network test
# ----------------------------
st.subheader("2) Network latency")
ping_url = st.text_input("Ping URL", value="https://example.com")

if st.button("Run Network Test"):
    results = []
    for i in range(5):
        t0 = time.perf_counter()
        ok = False
        code = None
        try:
            r = requests.get(ping_url, timeout=5)
            code = r.status_code
            ok = True
        except Exception:
            ok = False
        dt = (time.perf_counter() - t0) * 1000
        results.append((i + 1, ok, code, dt))
        time.sleep(0.3)

    st.table([
        {"try": n, "ok": ok, "status": code, "ms": round(dt, 1)}
        for n, ok, code, dt in results
    ])
    avg = sum(dt for _, _, _, dt in results) / len(results)
    st.info(f"Avg latency: {avg:.1f} ms")

st.divider()

# ----------------------------
# 3) Ollama inference test
# ----------------------------
st.subheader("3) Ollama inference (CPU)")
base_url = st.text_input("Ollama base URL", value="http://127.0.0.1:11434")
model_name = st.text_input("Model name", value="tinyllama:latest")

prompt = st.text_area(
    "Prompt",
    value="Explain what a neural network is in 2 short paragraphs (max 120 words).",
    height=110,
)

col1, col2 = st.columns(2)
with col1:
    max_tokens = st.slider("max_tokens (num_predict)", 64, 256, 160, step=16)
with col2:
    temperature = st.slider("temperature", 0.0, 1.0, 0.2, step=0.1)

client = LLMClient(base_url=base_url, model=model_name)

if st.button("Run LLM Test"):
    try:
        with st.spinner("Calling Ollama..."):
            result = client.chat(
                system_prompt="You are a concise tutor. Follow constraints strictly.",
                user_prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
            )
        st.success(f"LLM OK ✅ | {result['latency_ms']:.0f} ms")
        st.text_area("Output", value=result["text"], height=220)
    except Exception as e:
        st.error(f"LLM FAILED ❌ {e}")
        st.info("Make sure Ollama is running: `ollama serve` and the model name matches `ollama list`.")

