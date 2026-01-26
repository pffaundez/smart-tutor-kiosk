import streamlit as st

from app.core.content_loader import list_topics, load_topic
from app.core.scoring import score_quiz
from app.core.session import init_session_state, touch, maybe_reset
from app.llm.client import LLMClient
from app.core.retrieval.retriever import EmbeddingRetriever

# Inclusion of retriever for new function
retriever = EmbeddingRetriever()



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
# Step: Reinforcement (with embedding RAG)
# -------------------------

if st.session_state.step == "reinforce":
    touch(st)
    res = st.session_state.q1_result
    incorrect = res["incorrect_questions"]

    st.subheader("Reinforcement")
    st.write(f"You got **{res['correct']} / {res['total']}** correct.")

    # -------------------------
    # DEBUG 1: show incorrect questions (before generation)
    # -------------------------
    st.markdown("### Incorrect questions (debug)")
    for i, q in enumerate(incorrect, start=1):
        correct_text = q["options"][q["correctIndex"]]
        st.write(f"**{i}. {q['question']}**")
        st.write(f"Correct answer: **{correct_text}**")
        st.divider()

    # --- Build retrieval queries per mistake ---
    queries = []
    for q in incorrect:
        correct = q["options"][q["correctIndex"]]
        queries.append(f"{q['question']} Correct answer: {correct}")

    # --- Retrieve relevant chunks (deduplicate) ---
    retrieved = []
    seen = set()
    for qstr in queries:
        hits = retriever.retrieve(query=qstr, topic_id=topic["id"], k=2)
        for h in hits:
            if h["chunk_id"] not in seen:
                retrieved.append(h)
                seen.add(h["chunk_id"])

    source_pack = "\n\n".join([f"[{h['chunk_id']}]\n{h['text']}" for h in retrieved])

    # -------------------------
    # Generation + DEBUG 2: show retrieved chunks (after button press, before reinforcement text)
    # -------------------------
    if st.session_state.reinforcement == "":
        if big_button("Generate Reinforcement", "gen_reinforce"):
            # Show chunks used (debug) BEFORE calling / printing reinforcement
            st.markdown("### Retrieved chunks (debug)")
            if not retrieved:
                st.warning("No chunks retrieved.")
            else:
                for h in retrieved:
                    st.write(f"**{h['chunk_id']}** (score: {h.get('score', 0):.3f})")
                    st.write(h["text"])
                    st.divider()

            # Now generate reinforcement
            with st.spinner("Generating focused explanation..."):
                out = client.chat(sys_prompt, user_prompt, max_tokens=260, temperature=0.2)

            st.session_state.reinforcement = out["text"].strip()
            st.session_state.reinforce_latency = out["latency_ms"]
            st.rerun()

    else:
        st.info(f"Generated (latency {st.session_state.reinforce_latency:.0f} ms)")
        st.write(st.session_state.reinforcement)

        if big_button("Continue to Quiz 2", "to_quiz2"):
            st.session_state.step = "quiz2"
            st.rerun()


    sys_prompt = (
        "You are a corrective tutor in a public touchscreen kiosk. "
        "Your job is NOT to give a general lesson, but to FIX specific misunderstandings. "
        "Address the user directly using 'you'. "
        "Use ONLY the information in the SOURCE. "
        "Do NOT introduce any terms or methods that do not appear in the SOURCE. "
        "Do NOT repeat the SOURCE verbatim. Rephrase it in your own words. "
        "Do NOT include titles, headings, bullet points, or summaries. "
        "Write exactly 2 paragraphs, 120–150 words total. "
        "Focus ONLY on the concepts related to the user's incorrect answers. "
        "Do not explain concepts that were not answered incorrectly."
    )

    user_prompt = (
        "You answered some questions incorrectly. "
        "Rewrite only the parts of the explanation that are needed to fix those mistakes.\n\n"
        "Explain why the correct ideas are correct, using the SOURCE below, "
        "and ignore all other parts of the topic.\n\n"
        f"SOURCE (use only this information):\n<<<\n{source_pack}\n>>>\n\n"
        "Write the corrective explanation now."
    )




    if st.session_state.reinforcement == "":
        if big_button("Generate Reinforcement", "gen_reinforce"):
            with st.spinner("Generating focused explanation..."):
                out = client.chat(sys_prompt, user_prompt, max_tokens=260, temperature=0.2)
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
