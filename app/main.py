import streamlit as st

from app.core.content_loader import list_topics, load_topic
from app.core.scoring import score_quiz
from app.core.session import init_session_state, touch, maybe_reset
from app.llm.client import LLMClient
from app.core.retrieval.retriever import EmbeddingRetriever
from app.core.text_processor import format_easy_to_read

# Inclusion of retriever for new function
@st.cache_resource
def get_retriever():
    return EmbeddingRetriever()

retriever = get_retriever()

st.set_page_config(page_title="Smart Tutor Demo", layout="centered")

init_session_state(st)
maybe_reset(st)

st.title("Smart Tutor Demo (MVP - Local)")

llm1 = "llama3.1:latest"
llm2 = "llama2:7b-chat-q4_K_M"

# --- Global LLM settings (kiosk would hide this; demo shows it) ---
with st.expander("LLM Settings (demo only)", expanded=False):
    base_url = st.text_input("Ollama base URL", value="http://127.0.0.1:11434")
    # Model Selection: Llama 3.1
    model_name = st.text_input("Model name", value=llm2)
    st.caption("Ensure Ollama is running: `ollama serve`")

client = LLMClient(base_url=base_url, model=model_name)

# Options for re-explanation

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
            "Output only the two paragraphs. Start immediately with the first sentence."
        )
    },
    "simple_es": {
        "label": "Simple",
        "sys": (
            "You are a public-kiosk tutor. Address the user as 'you'. "
            "Explain in a simple english, short sentences, basic vocabulary. "
            "No titles, no bullet points, no numbered lists. "
            "Write exactly 2 short paragraphs, 110–140 words total. "
            "Use only the provided LESSON text. Rephrase it; do not copy verbatim."
        ),
    },
    "daily_analogies": {
        "label": "Analogies with Everyday Life",
        "sys": (
            "You are a public-kiosk tutor. Address the user as 'you'. "
            "Explain using everyday analogies to make the idea intuitive. "
            "Use ONLY analogies that preserve the meaning of the LESSON (do not add new facts). "
            "No titles, no bullet points, no numbered lists. "
            "Write exactly 2 short paragraphs, 120–160 words total. "
            "Use only the provided LESSON text as factual source; rephrase it."
        ),
    },
    "custom_domain_analogies": {
        "label": "Analogies with Custom Domain (WIP)",
        "sys": None, 
        "requires_input": True,
        "input_label": "Enter a domain (e.g., real estate, cooking, sports):"
    },
}


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

        # Cargar metadatos para mostrar títulos en lugar de IDs
    topics_with_titles = {}
    for tid in topics:
        topic_data = load_topic(tid)
        topics_with_titles[topic_data["title"]] = tid
    
    selected_title = st.selectbox("Choose a topic", list(topics_with_titles.keys()), index=0)
    topic_id = topics_with_titles[selected_title]

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
    st.subheader(f"Topic: {topic['title']}")
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

    # Build retrieval queries from mistakes (question + correct answer)
    queries = []
    for q in incorrect:
        correct = q["options"][q["correctIndex"]]
        queries.append(f"{q['question']} Correct answer: {correct}")


    # Retrieve chunks (deduplicate) using batch retrieval (fewer model encodes).
    retrieved = []
    seen = set()

    # Batch retrieve: one call encodes all queries at once and searches them all
    batch_hits = retriever.retrieve_batch(queries, topic_id=topic["id"], k=1)

    for hits in batch_hits:
        # hits is a list (up to k=1) of candidate chunks for that query
        for h in hits:
            if h["chunk_id"] not in seen:
                retrieved.append(h)
                seen.add(h["chunk_id"])
                break  # since we requested k=1, accept first unseen hit and move on

    retrieved = retrieved[:1]  # safety cap
    source_pack = " ".join([h["text"].strip() for h in retrieved]).strip()

    sys_prompt = (
        "You are a tutor in a public touchscreen kiosk. "
        "Address the user directly using 'you'. "
        "Write natural, continuous prose. "
        "Do not use titles, headings, bullet points, numbered lists, or section labels. "
        "Do not mention the quiz, questions, or answers. "
        "Use ONLY the SOURCE NOTES provided. "
        "Do not copy sentences verbatim from the SOURCE NOTES; rephrase them. "
        "Output MUST be exactly 2 paragraphs, 120–160 words total. "
        "Output MUST start immediately with the explanation (no preface). "
        "Do not use ':' at all."
    )

    user_prompt = (
        "You got some answers wrong. Explain again in a way that fixes those misunderstandings. "
        "Focus only on what was missed.\n\n"
        "SOURCE NOTES (use internally; do not quote or repeat):\n"
        f"<<<{source_pack}>>>\n\n"
        "Write the explanation now as two short paragraphs."
    )

    if st.session_state.reinforcement == "":
        if big_button("Generate Reinforcement", "gen_reinforce"):
            import time
            t0 = time.perf_counter()
            with st.spinner("Generating focused explanation..."):
                out = client.chat(sys_prompt, user_prompt, max_tokens=150, temperature=0.2)
            t_total = (time.perf_counter() - t0) * 1000
            
            st.session_state.reinforcement = out["text"].strip()
            st.session_state.reinforce_latency = out["latency_ms"]
            print(f"[main] Total reinforcement time: {t_total:.1f}ms, LLM latency: {out['latency_ms']:.1f}ms")
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
    #touch(st)
    touch(st)

    q1 = st.session_state.q1_result
    q2 = st.session_state.q2_result

    st.subheader("Results")
    if q1:
        st.write(f"Quiz 1: **{q1['correct']} / {q1['total']}**")
    if q2:
        st.write(f"Quiz 2: **{q2['correct']} / {q2['total']}**")

    still_weak = (q2 and q2["correct"] < max(1, q2["total"] - 1))

    if still_weak:
        st.warning("Result is still low. Choose a re-explanation format and try again.")

        # Choose format (scalable list)
        mode_labels = {v["label"]: k for k, v in REEXPLAIN_MODES.items()}
        chosen_label = st.radio(
            "Re-explain mode",
            options=list(mode_labels.keys()),
            horizontal=False,
        )
        chosen_mode = mode_labels[chosen_label]

        # Request additional input if mode requires it (e.g., custom domain for analogies)
        custom_domain = None
        if chosen_mode == "custom_domain_analogies":
            custom_domain = st.text_input(
                REEXPLAIN_MODES[chosen_mode]["input_label"],
                placeholder="e.g., real estate, cooking, sports, finance"
            )


        if big_button("Generate Re-explanation", "gen_reexplain"):
            topic_lesson = (topic["lesson"] if topic else "") or ""
            
            # Generate system prompt based on chosen mode
            if chosen_mode == "custom_domain_analogies":
                if not custom_domain:
                    st.error("Please enter a domain to continue.")
                    st.stop()
                
                sys_prompt = (
                    f"You are a public-kiosk tutor. Address the user as 'you'. "
                    f"Explain the concept using analogies and examples from the '{custom_domain}' domain. "
                    f"Use ONLY analogies from '{custom_domain}' that preserve the meaning of the LESSON (do not add new facts). "
                    f"No titles, no bullet points, no numbered lists. "
                    f"Write exactly 2 short paragraphs, 120–160 words total. "
                    f"Use only the provided LESSON text as factual source; rephrase it."
                )
            else:
                sys_prompt = REEXPLAIN_MODES[chosen_mode]["sys"]
            
            user_prompt = (
                "Rewrite the following LESSON according to the system instructions.\n\n"
                f"LESSON:\n<<<\n{topic_lesson}\n>>>\n"
            )

            with st.spinner("Generating..."):
                out = client.chat(sys_prompt, user_prompt, max_tokens=150, temperature=0.0)

            st.session_state.reexplain_text = out["text"].strip()
        
            # Aplicar procesamiento si es modo easy_to_read
            if chosen_mode == "easy_to_read":
                st.session_state.reexplain_text = format_easy_to_read(st.session_state.reexplain_text)
        
            st.session_state.reexplain_latency = out["latency_ms"]            

            #--------------------------------------------

        # Show generated text (if any)
        if st.session_state.reexplain_text:
            st.info(f"Generated (latency {st.session_state.reexplain_latency:.0f} ms)")
            st.write(st.session_state.reexplain_text)

            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("Try Quiz Again", use_container_width=True):
                    # reset quizzes + reinforcement, go back to quiz1
                    st.session_state.answers_q1 = {}
                    st.session_state.answers_q2 = {}
                    st.session_state.q1_result = None
                    st.session_state.q2_result = None
                    st.session_state.reinforcement = ""
                    st.session_state.reexplain_text = ""
                    st.session_state.step = "quiz1"
                    st.rerun()

            with col_b:
                if st.button("Back to Lesson", use_container_width=True):
                    st.session_state.step = "lesson"
                    st.rerun()
    else:
        st.success("Good job! ✅")
