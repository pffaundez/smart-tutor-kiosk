import streamlit as st

from app.core.content_loader import list_topics, load_topic
from app.core.scoring import score_quiz
from app.core.session import init_session_state, touch, maybe_reset
from app.llm.client import LLMClient


st.set_page_config(page_title="Smart Tutor Demo", layout="centered")

init_session_state(st)
maybe_reset(st)

st.title("Smart Tutor Demo (Local)")

# --- Global LLM settings (kiosk would hide this; demo shows it) ---
with st.expander("LLM Settings (demo only)", expanded=False):
    base_url = st.text_input("Ollama base URL", value="http://127.0.0.1:11434")
    model_name = st.text_input("Model name", value="tinyllama:latest")
    st.caption("Ensure Ollama is running: `ollama serve`")

client = LLMClient(base_url=base_url, model=model_name)

def big_button(label, key):
    return st.button(label, key=key, use_container_width=True)

# -------------------------
# Step: Select topic
# -------------------------
if st.session_state.step == "select":
    touch(st)
    topics = list_topics()

    if not topics:
        st.error("No topics found in content/topics/")
        st.stop()

    # For now you can keep only topic001, but this scales automatically.
    topic_id = st.selectbox("Choose a topic", topics, index=0)

    if big_button("Start", "start"):
        st.session_state.topic_id = topic_id
        st.session_state.step = "lesson"
        st.rerun()

# Load current topic
topic = load_topic(st.session_state.topic_id) if st.session_state.topic_id else None

# -------------------------
# Step: Lesson
# -------------------------
if st.session_state.step == "lesson":
    touch(st)
    st.subheader(f"Topic: {topic['id']}")
    st.write(topic["lesson"] or "_lesson.md not found_")

    if big_button("Take Quiz", "to_quiz1"):
        st.session_state.step = "quiz1"
        st.rerun()

# -------------------------
# Step: Quiz 1
# -------------------------
if st.session_state.step == "quiz1":
    touch(st)
    quiz = topic["quiz_1"]
    if not quiz:
        st.error("quiz_1.json not found for this topic.")
        st.stop()

    st.subheader("Quiz 1")

    answers = {}
    for q in quiz["questions"]:
        st.write(f"**{q['question']}**")
        choice = st.radio(
            label="",
            options=list(range(len(q["options"]))),
            format_func=lambda i, opts=q["options"]: opts[i],
            key=f"q1_{q['id']}",
        )
        answers[q["id"]] = choice
        st.divider()

    if big_button("Submit Quiz 1", "submit_q1"):
        st.session_state.answers_q1 = answers
        st.session_state.q1_result = score_quiz(quiz, answers)

        incorrect = st.session_state.q1_result["incorrect_questions"]
        if len(incorrect) == 0:
            st.session_state.step = "quiz2"
        else:
            st.session_state.step = "reinforce"

        st.rerun()

# -------------------------
# Step: Reinforcement (LLM)
# -------------------------
if st.session_state.step == "reinforce":
    touch(st)
    res = st.session_state.q1_result
    incorrect = res["incorrect_questions"]

    st.subheader("Reinforcement")
    st.write(f"You got **{res['correct']} / {res['total']}** correct.")

    # Build reinforcement prompt grounded in source.md
    source = topic["source"] or topic["lesson"]  # fallback if no source.md
    missed_summary = "\n".join(
        [
            f"- Focus concept: {q.get('conceptTag', 'unknown')}\n"
            f"  Question topic: {q['question']}\n"
            f"  Correct idea: {q['options'][q['correctIndex']]}"
            for q in incorrect
        ]
    )

    sys_prompt = (
        "You are a tutor in a public touchscreen kiosk. "
        "Address the user directly in second person (use 'you'). "
        "Be concise and factual. "
        "Use ONLY the provided SOURCE text. "
        "Do not add new facts or examples. "
        "Explain ALL the incorrect answers, not just one. "
        "Write each explanation in short paragraphs, maximum 100 words each."
    )

    user_prompt = (
        "You answered several questions incorrectly.\n"
        "Re-explain the topic focusing on ALL the concepts related to the mistakes listed in the 'missed summary' below.\n"
        "Address the user directly (use 'you'), not in third person.\n\n"
        f"SOURCE:\n<<<\n{source}\n>>>\n\n"
        f"INCORRECT QUESTIONS AND CORRECT IDEAS TO REINFORCE:\n{missed_summary}\n\n"
        "Write the reinforcement now, covering all of them."
    )

    if st.session_state.reinforcement == "":
        if big_button("Generate Reinforcement", "gen_reinforce"):
            with st.spinner("Generating..."):
                out = client.chat(sys_prompt, user_prompt, max_tokens=220, temperature=0.2)
            st.session_state.reinforcement = out["text"].strip()
            st.session_state.reinforce_latency = out["latency_ms"]
            st.rerun()
    else:
        st.info(f"Generated (latency {st.session_state.reinforce_latency:.0f} ms)")
        st.write(st.session_state.reinforcement)

        if big_button("Continue to Quiz 2", "to_quiz2"):
            st.session_state.step = "quiz2"
            st.rerun()

# -------------------------
# Step: Quiz 2
# -------------------------
if st.session_state.step == "quiz2":
    touch(st)
    quiz = topic["quiz_2"]
    if not quiz:
        st.error("quiz_2.json not found for this topic.")
        st.stop()

    st.subheader("Quiz 2 (Extra)")

    answers = {}
    for q in quiz["questions"]:
        st.write(f"**{q['question']}**")
        choice = st.radio(
            label="",
            options=list(range(len(q["options"]))),
            format_func=lambda i, opts=q["options"]: opts[i],
            key=f"q2_{q['id']}",
        )
        answers[q["id"]] = choice
        st.divider()

    if big_button("Submit Quiz 2", "submit_q2"):
        st.session_state.answers_q2 = answers
        st.session_state.q2_result = score_quiz(quiz, answers)
        st.session_state.step = "done"
        st.rerun()

# -------------------------
# Step: Done
# -------------------------
if st.session_state.step == "done":
    touch(st)
    q1 = st.session_state.q1_result
    q2 = st.session_state.q2_result

    st.subheader("Results")
    if q1:
        st.write(f"Quiz 1: **{q1['correct']} / {q1['total']}**")
    if q2:
        st.write(f"Quiz 2: **{q2['correct']} / {q2['total']}**")

    # Offer re-explain if still weak
    still_weak = (q2 and q2["correct"] < max(1, q2["total"] - 1))  # simple threshold
    if still_weak:
        st.warning("Result is still low. You can re-explain the topic and try again.")
        if big_button("Re-explain", "reexplain"):
            st.session_state.reinforcement = ""
            st.session_state.step = "lesson"
            st.rerun()
    else:
        st.success("Good job! ✅")

    if big_button("Start Over", "reset"):
        st.session_state.step = "select"
        st.session_state.topic_id = None
        st.session_state.answers_q1 = {}
        st.session_state.answers_q2 = {}
        st.session_state.q1_result = None
        st.session_state.q2_result = None
        st.session_state.reinforcement = ""
        st.rerun()
