import streamlit as st

from app.core.content_loader import list_topics, load_topic
from app.core.scoring import score_quiz
from app.core.session import init_session_state, touch, maybe_reset
from app.llm.client import LLMClient
from app.core.reexplain_service import generate_reexplanation
from app.prompts.reexplain_modes import (
    get_mode_keys,
    get_label,
    requires_input,
    get_input_label,
)


DEBUG_MODE = False

st.set_page_config(
    page_title="Smart Tutor Demo",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
        .main { padding-top: 1.2rem; padding-bottom: 2rem; }
        h1, h2, h3 { text-align: center; }

        .center-box {
            max-width: 850px;
            margin: 0 auto;
        }

        .big-text {
            font-size: 1.18rem;
            line-height: 1.75;
        }

        .result-box {
            padding: 1rem 1.2rem;
            border-radius: 14px;
            background-color: rgba(240,240,240,0.08);
            margin-top: 1rem;
            margin-bottom: 1rem;
        }

        .subtle-center {
            text-align: center;
            opacity: 0.9;
        }

        .mode-help {
            text-align: center;
            margin-top: 0.8rem;
            margin-bottom: 1rem;
            font-size: 1rem;
            opacity: 0.9;
        }

        .stButton > button {
            width: 100%;
            min-height: 3.4rem;
            font-size: 1.02rem;
            border-radius: 12px;
            white-space: normal;
        }

        .mode-buttons .stButton > button {
            min-height: 4.3rem;
            font-size: 0.98rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

init_session_state(st)
maybe_reset(st)

llm3 = "qwen2.5:3b"

if DEBUG_MODE:
    with st.expander("LLM Settings", expanded=False):
        base_url = st.text_input("Base URL", value="http://127.0.0.1:11434")
        model_name = st.text_input("Model", value=llm3)
else:
    base_url = "http://127.0.0.1:11434"
    model_name = llm3

client = LLMClient(base_url=base_url, model=model_name)


def big_button(label, key, disabled=False):
    return st.button(label, key=key, use_container_width=True, disabled=disabled)


def reset_reexplain_state():
    st.session_state.reexplain_text = ""
    st.session_state.reexplain_latency = None
    st.session_state.reexplain_mode = None


def display_mode_buttons(prefix: str):
    mode_keys = get_mode_keys()
    cols = st.columns(len(mode_keys))

    short_labels = {
        "easy_to_read": "Easy-to-Read",
        "simple": "Simple",
        "daily_analogies": "Examples",
        "custom_domain_analogies": "Custom Analogies",
    }

    st.markdown("<p class='mode-help'>Choose one of these explanation options.</p>", unsafe_allow_html=True)
    st.markdown('<div class="mode-buttons">', unsafe_allow_html=True)

    for col, key in zip(cols, mode_keys):
        label = short_labels.get(key, get_label(key))
        selected = st.session_state.reexplain_mode == key
        btn = f"✅ {label}" if selected else label

        with col:
            if st.button(btn, key=f"{prefix}_{key}", use_container_width=True):
                st.session_state.reexplain_mode = key
                st.session_state.reexplain_text = ""
                st.session_state.reexplain_latency = None
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


# -------------------------
# Step: Select
# -------------------------
if st.session_state.step == "select":
    touch(st)
    topics = list_topics()

    if not topics:
        st.error("No topics found in content/topics/")
        st.stop()

    topics_with_titles = {}
    for tid in topics:
        t = load_topic(tid)
        topics_with_titles[t.get("title", tid)] = tid

    st.markdown('<div class="center-box">', unsafe_allow_html=True)
    st.title("Smart Tutor")
    st.markdown(
        "<p class='subtle-center big-text'>Choose a topic and start learning.</p>",
        unsafe_allow_html=True,
    )

    selected = st.selectbox("Topic", list(topics_with_titles.keys()))
    topic_id = topics_with_titles[selected]

    if big_button("Start", "start"):
        st.session_state.topic_id = topic_id
        st.session_state.step = "lesson"
        reset_reexplain_state()
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

topic = load_topic(st.session_state.topic_id) if st.session_state.topic_id else None


# -------------------------
# Lesson
# -------------------------
if st.session_state.step == "lesson":
    touch(st)

    st.markdown('<div class="center-box">', unsafe_allow_html=True)
    st.subheader(topic["title"])
    st.markdown(f"<div class='big-text'>{topic['lesson']}</div>", unsafe_allow_html=True)

    if big_button("Take Quiz", "to_q1"):
        st.session_state.step = "quiz1"
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


# -------------------------
# Quiz 1
# -------------------------
if st.session_state.step == "quiz1":
    touch(st)

    quiz = topic["quiz_1"]
    answers = {}

    st.markdown('<div class="center-box">', unsafe_allow_html=True)
    st.subheader("Quiz 1")

    for q in quiz["questions"]:
        st.write(f"**{q['question']}**")
        choice = st.radio(
            "",
            range(len(q["options"])),
            format_func=lambda i, opts=q["options"]: opts[i],
            key=f"q1_{q['id']}",
        )
        answers[q["id"]] = choice
        st.divider()

    if big_button("Submit", "submit_q1"):
        st.session_state.q1_result = score_quiz(quiz, answers)
        incorrect = st.session_state.q1_result["incorrect_questions"]

        st.session_state.step = "quiz2" if not incorrect else "reexplain_q1"
        reset_reexplain_state()
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


# -------------------------
# Re-explain (after Quiz 1)
# -------------------------
if st.session_state.step == "reexplain_q1":
    touch(st)

    q1 = st.session_state.q1_result

    st.markdown('<div class="center-box">', unsafe_allow_html=True)
    st.subheader("Let's explain it differently")
    st.markdown(
        f"<p class='subtle-center'>You got <strong>{q1['correct']} / {q1['total']}</strong> correct in Quiz 1.</p>",
        unsafe_allow_html=True,
    )

    display_mode_buttons("pick_q1")
    selected_key = st.session_state.reexplain_mode

    custom_domain = None
    if selected_key and requires_input(selected_key):
        custom_domain = st.text_input(get_input_label(selected_key))

    if not selected_key:
        st.info("Select an explanation style first.")

    if big_button("Generate New Explanation", "gen_q1", disabled=selected_key is None):
        lesson = topic["lesson"]
        text, latency = generate_reexplanation(
            client, lesson, selected_key, custom_domain
        )
        st.session_state.reexplain_text = text
        st.session_state.reexplain_latency = latency

    if st.session_state.reexplain_text:
        st.info(f"Generated explanation in {st.session_state.reexplain_latency:.0f} ms")
        st.markdown("<div class='result-box'>", unsafe_allow_html=True)
        st.markdown(f"<div class='big-text'>{st.session_state.reexplain_text}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Continue", key="to_q2", use_container_width=True):
                reset_reexplain_state()
                st.session_state.step = "quiz2"
                st.rerun()

        with col_b:
            if st.button("Back to Original Lesson", key="back_lesson_q1", use_container_width=True):
                reset_reexplain_state()
                st.session_state.step = "lesson"
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


# -------------------------
# Quiz 2
# -------------------------
if st.session_state.step == "quiz2":
    touch(st)

    quiz = topic["quiz_2"]
    answers = {}

    st.markdown('<div class="center-box">', unsafe_allow_html=True)
    st.subheader("Quiz 2")

    for q in quiz["questions"]:
        st.write(f"**{q['question']}**")
        choice = st.radio(
            "",
            range(len(q["options"])),
            format_func=lambda i, opts=q["options"]: opts[i],
            key=f"q2_{q['id']}",
        )
        answers[q["id"]] = choice
        st.divider()

    if big_button("Submit", "submit_q2"):
        st.session_state.q2_result = score_quiz(quiz, answers)
        st.session_state.step = "done"
        reset_reexplain_state()
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


# -------------------------
# Done
# -------------------------
if st.session_state.step == "done":
    touch(st)

    q2 = st.session_state.q2_result

    st.markdown('<div class="center-box">', unsafe_allow_html=True)
    st.subheader("Results")
    st.write(f"Score: {q2['correct']} / {q2['total']}")

    if q2["correct"] < q2["total"] - 1:
        st.warning("Let's try another explanation.")

        display_mode_buttons("pick_done")
        selected_key = st.session_state.reexplain_mode

        custom_domain = None
        if selected_key and requires_input(selected_key):
            custom_domain = st.text_input(get_input_label(selected_key))

        if not selected_key:
            st.info("Select an explanation style first.")

        if big_button("Generate Re-explanation", "reexp", disabled=selected_key is None):
            lesson = topic["lesson"]
            text, latency = generate_reexplanation(
                client, lesson, selected_key, custom_domain
            )
            st.session_state.reexplain_text = text
            st.session_state.reexplain_latency = latency

        if st.session_state.reexplain_text:
            st.info(f"Generated explanation in {st.session_state.reexplain_latency:.0f} ms")
            st.markdown("<div class='result-box'>", unsafe_allow_html=True)
            st.markdown(f"<div class='big-text'>{st.session_state.reexplain_text}</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            if big_button("Try Again", "retry"):
                st.session_state.step = "quiz1"
                reset_reexplain_state()
                st.rerun()

    else:
        st.success("Great job!")

    if big_button("Start Over", "reset"):
        st.session_state.step = "select"
        reset_reexplain_state()
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)