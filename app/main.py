import streamlit as st

from app.core.content_loader import list_topics, load_topic
from app.core.scoring import score_quiz
from app.core.session import init_session_state, touch, maybe_reset
from app.llm.client import LLMClient
from app.core.reexplain_service import generate_reexplanation
from app.core.text_processor import bionic_reading_html
from app.prompts.reexplain_modes import (
    get_mode_keys,
    get_label,
    requires_input,
    get_input_label,
)

DEBUG_MODE = False

st.set_page_config(
    page_title="Smart Tutor Demo",
    layout="wide",
    initial_sidebar_state="collapsed",
)


st.markdown(
    """
    <style>
        .stApp {
            background: #f5f7fb;
        }

        .main .block-container {
            max-width: 1120px;
            padding-top: 1.5rem;
            padding-bottom: 2rem;
        }

        h1, h2, h3, h4, h5, h6 {
            color: #111827 !important;
        }

        /* ===== TOP BAR ===== */
        .smart-topbar {
            margin-bottom: 1rem;
        }

        .smart-brand {
            display: flex;
            flex-direction: column;
            gap: 0.1rem;
        }

        .smart-title {
            font-size: 2rem;
            font-weight: 800;
            line-height: 1.1;
            color: #111827 !important;
        }

        .smart-subtitle {
            font-size: 0.95rem;
            color: #6b7280 !important;
        }

        /* ===== STEPPER ===== */
        .smart-stepper {
            display: grid;
            grid-template-columns: repeat(6, minmax(0, 1fr));
            gap: 0.75rem;
            margin: 1rem 0 1.5rem 0;
        }

        .smart-step {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 16px;
            padding: 0.9rem 0.75rem;
            text-align: center;
            font-size: 0.92rem;
            font-weight: 700;
            color: #6b7280 !important;
            box-shadow: 0 4px 18px rgba(17, 24, 39, 0.04);
        }

        .smart-step.active {
            border: 2px solid #2563eb;
            background: #f8fbff;
            color: #111827 !important;
            box-shadow: 0 8px 22px rgba(37, 99, 235, 0.10);
        }

        .smart-step.done {
            background: #eff6ff;
            border: 1px solid #bfdbfe;
            color: #1d4ed8 !important;
        }

        /* ===== GENERIC TEXT TOKENS ===== */
        .smart-section-title {
            font-size: 1.9rem;
            font-weight: 800;
            margin-bottom: 0.35rem;
            color: #111827 !important;
        }

        .smart-section-subtitle {
            font-size: 1.05rem;
            margin-bottom: 1.15rem;
            color: #6b7280 !important;
        }

        .smart-helper {
            font-size: 0.96rem;
            margin-bottom: 1rem;
            color: #6b7280 !important;
        }

        .smart-hero {
            text-align: center;
            padding: 0.5rem 0 0.75rem 0;
        }

        .smart-hero-title {
            font-size: 2.2rem;
            font-weight: 800;
            margin-bottom: 0.35rem;
            color: #111827 !important;
        }

        .smart-hero-subtitle {
            font-size: 1.05rem;
            max-width: 760px;
            margin: 0 auto;
            line-height: 1.6;
            color: #6b7280 !important;
        }

        /* ===== CARDS ===== */
        .smart-grid-card {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 18px;
            padding: 1rem;
            min-height: 150px;
            box-shadow: 0 4px 18px rgba(17, 24, 39, 0.04);
            margin-bottom: 0.75rem;
        }

        .smart-grid-card.selected {
            border: 2px solid #2563eb;
            background: #f8fbff;
        }

        .smart-card-title {
            font-size: 1.06rem;
            font-weight: 700;
            margin-bottom: 0.25rem;
            color: #111827 !important;
        }

        .smart-card-text {
            font-size: 0.96rem;
            line-height: 1.5;
            color: #6b7280 !important;
        }

        /* ===== LESSON HERO — FINAL FIX ===== */
        .smart-lesson-markdown {
            max-width: 820px;
            margin: 1.25rem auto 0 auto;
        }

        /* 🔥 Aplica a TODO sin depender de <p> */
        .smart-lesson-markdown .lesson-content,
        .smart-lesson-markdown .lesson-content * {
            font-size: 1.22rem !important;
            line-height: 1.95 !important;
            color: #111827 !important;
        }

        /* Espaciado consistente */
        .smart-lesson-markdown .lesson-content p {
            margin-bottom: 1.15rem;
        }

        /* Headings */
        .smart-lesson-markdown .lesson-content h1,
        .smart-lesson-markdown .lesson-content h2,
        .smart-lesson-markdown .lesson-content h3 {
            font-weight: 800 !important;
            margin-top: 1.8rem !important;
            margin-bottom: 0.7rem !important;
        }

        .smart-lesson-markdown .lesson-content h1 {
            font-size: 2rem !important;
        }

        .smart-lesson-markdown .lesson-content h2 {
            font-size: 1.6rem !important;
        }

        .smart-lesson-markdown .lesson-content h3 {
            font-size: 1.35rem !important;
        }

        /* Listas */
        .smart-lesson-markdown .lesson-content ul,
        .smart-lesson-markdown .lesson-content ol {
            padding-left: 1.6rem;
            margin-bottom: 1.1rem;
        }

        /* Blockquote */
        .smart-lesson-markdown .lesson-content blockquote {
            border-left: 4px solid #dbeafe;
            background: #f8fbff;
            padding: 0.9rem 1rem;
            margin: 1.2rem 0;
            border-radius: 0 14px 14px 0;
            color: #374151 !important;
        }

        /* ❌ IMPORTANTE: eliminar esto si lo tienes */
        .smart-lesson-markdown .lesson-content p:first-child {
            font-size: 1.3rem !important;
        }


   

        /* ===== QUIZ ===== */
        .smart-question-card {
            background: #fafafa;
            border: 1px solid #e5e7eb;
            border-radius: 18px;
            padding: 1rem;
            margin-bottom: 1rem;
        }

        .smart-question-label {
            font-size: 0.82rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-bottom: 0.45rem;
            color: #2563eb !important;
        }

        .smart-question-text {
            font-size: 1.12rem;
            line-height: 1.6;
            font-weight: 700;
            margin-bottom: 0.9rem;
            color: #111827 !important;
        }

        .smart-question-card p,
        .smart-question-card span,
        .smart-question-card strong,
        .smart-question-card label,
        .smart-question-card li {
            color: #111827 !important;
        }

        /* ===== RE-EXPLAIN QUIZ SCORE ===== */
        .smart-score-banner {
            background: linear-gradient(135deg, #eff6ff 0%, #ffffff 100%);
            border: 1px solid #dbeafe;
            border-radius: 20px;
            padding: 1rem 1.2rem;
            margin-bottom: 1rem;
            box-shadow: 0 6px 20px rgba(37, 99, 235, 0.08);
        }

        .smart-score-label {
            font-size: 0.88rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #2563eb !important;
            margin-bottom: 0.3rem;
        }

        .smart-score-value {
            font-size: 2rem;
            font-weight: 800;
            line-height: 1.1;
            color: #111827 !important;
            margin-bottom: 0.25rem;
        }

        .smart-score-caption {
            font-size: 1rem;
            color: #6b7280 !important;
            line-height: 1.5;
        }



        /* ===== MODE HELP ===== */
        .smart-mode-help {
            text-align: left;
            margin-top: 0.2rem;
            margin-bottom: 1rem;
            font-size: 0.98rem;
            color: #6b7280 !important;
        }

        /* ===== RESULTS ===== */
        .smart-result-hero {
            background: linear-gradient(135deg, #eff6ff 0%, #ffffff 100%);
            border: 1px solid #dbeafe;
            border-radius: 22px;
            padding: 1.25rem;
            margin-bottom: 1rem;
        }

        .smart-result-title {
            font-size: 1.6rem;
            font-weight: 800;
            margin-bottom: 0.25rem;
            color: #111827 !important;
        }

        .smart-result-score {
            font-size: 2rem;
            font-weight: 800;
            margin-bottom: 0.25rem;
            color: #1d4ed8 !important;
        }

        .smart-result-subtitle {
            font-size: 1rem;
            color: #6b7280 !important;
        }

        .smart-stat-card {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 18px;
            padding: 1rem;
            box-shadow: 0 4px 18px rgba(17, 24, 39, 0.04);
        }

        .smart-stat-label {
            font-size: 0.9rem;
            margin-bottom: 0.25rem;
            color: #6b7280 !important;
        }

        .smart-stat-value {
            font-size: 1.35rem;
            font-weight: 800;
            color: #111827 !important;
        }

        /* ===== OUTPUT ===== */
        .smart-output-box {
            padding: 1.5rem 1.8rem;
            border-radius: 20px;
            background: #ffffff;
            border: 1px solid #e5e7eb;
            margin-top: 1.2rem;
            margin-bottom: 1.2rem;
            box-shadow: 0 8px 30px rgba(17, 24, 39, 0.06);
        }

        .smart-output-title {
            font-size: 1.15rem;
            font-weight: 700;
            margin-bottom: 0.6rem;
            color: #111827 !important;
        }

        .smart-output-text {
            font-size: 1.2rem;
            line-height: 1.95;
            max-width: 760px;
            margin: 0 auto;
            color: #111827 !important;
        }

        .smart-footer {
            text-align: center;
            font-size: 0.86rem;
            margin-top: 1rem;
            color: #9ca3af !important;
        }

        /* ===== BUTTON BASE ===== */
        div.stButton > button {
            min-height: 3.3rem;
            font-size: 1rem;
            border-radius: 14px;
            white-space: normal;
            font-weight: 700;
        }

        .mode-buttons .stButton > button {
            min-height: 4.1rem;
            font-size: 0.97rem;
        }

        .quiz-options-row .stButton > button {
            min-height: 5.2rem;
            font-size: 0.96rem;
            text-align: left;
            padding: 0.8rem;
        }

        /* ===== ALL BUTTON TEXT WHITE, ONLY INSIDE BUTTONS ===== */
        div.stButton > button,
        div.stButton > button *,
        .quiz-options-row div.stButton > button,
        .quiz-options-row div.stButton > button * {
            color: #ffffff !important;
        }

        div[data-testid="stHorizontalBlock"] > div {
            align-self: stretch;
        }
        /* ===== BIONIC READING ===== */
        .smart-lesson-markdown.bionic .lesson-content p,
        .smart-lesson-markdown.bionic .lesson-content li {
            font-size: 1.22rem !important;
            line-height: 2 !important;
            color: #111827 !important;
        }

        .smart-lesson-markdown.bionic .lesson-content strong {
            font-weight: 800 !important;
            color: #111827 !important;
        }

        .smart-bionic-toggle-label {
            font-size: 0.95rem;
            color: #6b7280 !important;
            margin-bottom: 0.75rem;
        }

        /* ===== BIONIC TOGGLE FIX ===== */

        /* Label del toggle */
        div[data-testid="stToggle"] label {
            color: #111827 !important;
            font-weight: 600;
            font-size: 1rem;
        }

        /* Fondo del switch */
        div[data-testid="stToggle"] div[role="switch"] {
            background-color: #e5e7eb !important;
        }

        /* Estado activo */
        div[data-testid="stToggle"] div[role="switch"][aria-checked="true"] {
            background-color: #2563eb !important;
        }

        /* Bolita del toggle */
        div[data-testid="stToggle"] div[role="switch"]::before {
            background-color: #ffffff !important;
        }



    </style>
    """,
    unsafe_allow_html=True,
)


init_session_state(st)
maybe_reset(st)

if "lesson_bionic" not in st.session_state:
    st.session_state.lesson_bionic = False

llm2 = "qwen3:0.6b"
llm3 = "qwen2.5:3b"
#llm3 = "qwen2.5:7b"

if DEBUG_MODE:
    with st.expander("LLM Settings", expanded=False):
        base_url = st.text_input("Base URL", value="http://127.0.0.1:11434")
        model_name = st.text_input("Model", value=llm3)
else:
    base_url = "http://127.0.0.1:11434"
    model_name = llm3

client = LLMClient(base_url=base_url, model=model_name)


def big_button(label, key, disabled=False, type="secondary"):
    return st.button(
        label,
        key=key,
        use_container_width=True,
        disabled=disabled,
        type=type,
    )


def reset_reexplain_state():
    st.session_state.reexplain_text = ""
    st.session_state.reexplain_latency = None
    st.session_state.reexplain_mode = None


def reset_app_state():
    st.session_state.topic_id = None
    st.session_state.q1_result = None
    st.session_state.q2_result = None
    st.session_state.reexplain_text = ""
    st.session_state.reexplain_latency = None
    st.session_state.reexplain_mode = None
    st.session_state.step = "select"

    for key in list(st.session_state.keys()):
        if (
            key.startswith("q1_")
            or key.startswith("q2_")
            or key.startswith("pick_q1_")
            or key.startswith("pick_done_")
        ):
            del st.session_state[key]


def render_nav_buttons(back_step=None, back_label="Back", home_label="Home"):
    col1, col2, col3 = st.columns([1, 6, 1])

    with col1:
        if st.button(
            back_label,
            key=f"back_{st.session_state.step}",
            disabled=back_step is None,
        ):
            if back_step is not None:
                st.session_state.step = back_step
                st.rerun()

    with col3:
        if st.button(
            home_label,
            key=f"home_{st.session_state.step}",
        ):
            reset_app_state()
            st.rerun()


def render_topbar():
    col1, col2 = st.columns([6, 1])

    with col1:
        st.markdown(
            """
            <div class="smart-brand">
                <div class="smart-title">🧠 Smart Tutor 🦉</div>
                <div class="smart-subtitle">Interactive learning demo</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.image("app/assets/ki_owl.png", width=160)



def render_footer():
    col_left, col_center, col_right = st.columns([2, 4, 2])

    # 🔵 DICE logo (bottom-left)
    with col_left:
        st.image("app/assets/dice.png", width=140)

    # 🧠 Footer text (center)
    with col_center:
        st.markdown(
            "<div class='smart-footer'>Local-first tutoring experience</div>",
            unsafe_allow_html=True,
        )

    # 🇩🇪 Bundesministerium (bottom-right)
    #with col_right:
    #    st.image("app/assets/bundes.png", width=260)


def render_section_header(title: str, subtitle: str | None = None):
    st.markdown(f"<div class='smart-section-title'>{title}</div>", unsafe_allow_html=True)
    if subtitle:
        st.markdown(
            f"<div class='smart-section-subtitle'>{subtitle}</div>",
            unsafe_allow_html=True,
        )


def render_stepper():
    step_map = {
        "select": 0,
        "lesson": 1,
        "quiz1": 2,
        "reexplain_q1": 3,
        "quiz2": 4,
        "done": 5,
    }

    labels = ["Topic", "Lesson", "Quiz 1", "Re-explain", "Quiz 2", "Results"]
    current_idx = step_map.get(st.session_state.step, 0)

    html = ['<div class="smart-stepper">']
    for idx, label in enumerate(labels):
        css_class = "smart-step"
        if idx < current_idx:
            css_class += " done"
        elif idx == current_idx:
            css_class += " active"
        html.append(f'<div class="{css_class}">{label}</div>')
    html.append("</div>")

    st.markdown("".join(html), unsafe_allow_html=True)


def display_mode_buttons(prefix: str):
    mode_keys = get_mode_keys()
    cols = st.columns(len(mode_keys))

    short_labels = {
        "easy_to_read": "Easy-to-Read",
        "simple": "Simple",
        "daily_analogies": "Examples",
        "custom_domain_analogies": "Custom Analogies",
    }

    short_desc = {
        "easy_to_read": "Clearer wording with simpler structure.",
        "simple": "A shorter, more direct version.",
        "daily_analogies": "Uses familiar real-world examples.",
        "custom_domain_analogies": "Connects the lesson to an area you choose.",
    }

    emojis = {
        "easy_to_read": "📘",
        "simple": "✨",
        "daily_analogies": "🔄",
        "custom_domain_analogies": "🎯",
    }

    st.markdown(
        "<div class='smart-mode-help'>Choose one explanation option.</div>",
        unsafe_allow_html=True,
    )

    for col, key in zip(cols, mode_keys):
        label = short_labels.get(key, get_label(key))
        desc = short_desc.get(key, "")
        emoji = emojis.get(key, "✨")
        selected = st.session_state.reexplain_mode == key

        with col:
            card_class = "smart-grid-card selected" if selected else "smart-grid-card"
            st.markdown(
                f"""
                <div class="{card_class}">
                    <div class="smart-card-title">{emoji} {label}</div>
                    <div class="smart-card-text">{desc}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            button_label = f"Selected: {label}" if selected else f"Choose {label}"
            if st.button(button_label, key=f"{prefix}_{key}", use_container_width=True):
                st.session_state.reexplain_mode = key
                st.session_state.reexplain_text = ""
                st.session_state.reexplain_latency = None
                st.rerun()

def render_topic_cards(topics_with_titles):
    selected_topic_id = st.session_state.get("topic_id")
    topic_items = list(topics_with_titles.items())

    total_cards = len(topic_items) + 1
    n_cols = min(3, max(1, total_cards))
    cols = st.columns(n_cols)

    # -------------------------
    # Existing topic cards
    # -------------------------
    for idx, (title, tid) in enumerate(topic_items):
        topic_data = load_topic(tid)
        description = (
            topic_data.get("description")
            or topic_data.get("summary")
            or "Short topic introduction."
        )
        selected = selected_topic_id == tid

        with cols[idx % n_cols]:
            card_class = "smart-grid-card selected" if selected else "smart-grid-card"

            st.markdown(
                f"""
                <div class="{card_class}">
                    <div class="smart-card-title">{title}</div>
                    <div class="smart-card-text">{description}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            btn_label = f"Selected: {title}" if selected else f"Choose {title}"
            if st.button(btn_label, key=f"topic_{tid}", use_container_width=True):
                st.session_state.topic_id = tid
                st.rerun()

    # -------------------------
    # Coming Soon card (NO HTML)
    # -------------------------
    coming_idx = len(topic_items)

    with cols[coming_idx % n_cols]:
        st.markdown("**Future feature**")
        st.markdown("### ✨ Coming Soon")

        st.write(
            "Soon you will be able to type any topic and let Smart Tutor "
            "generate a lesson and quiz for you."
        )

        st.text_input(
            "Topic idea",
            value="Type any topic...",
            disabled=True,
            key="coming_soon_topic_input",
            label_visibility="collapsed",
        )

        st.button(
            "Generate (soon)",
            disabled=True,
            use_container_width=True,
            key="coming_soon_generate",
        )

def render_quiz_question(question, question_number: int, answer_prefix: str):
    question_id = question["id"]
    options = question["options"]
    option_letters = ["A", "B", "C", "D", "E", "F"]

    selected_value = st.session_state.get(f"{answer_prefix}_{question_id}", None)

    st.markdown('<div class="smart-question-card">', unsafe_allow_html=True)
    st.markdown(
        f"<div class='smart-question-label'>Question {question_number}</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div class='smart-question-text'>{question['question']}</div>",
        unsafe_allow_html=True,
    )

    st.markdown('<div class="quiz-options-row">', unsafe_allow_html=True)
    cols = st.columns(len(options))

    for idx, option in enumerate(options):
        letter = option_letters[idx]
        selected = selected_value == idx
        button_text = f"{letter}. {option}"
        button_type = "primary" if selected else "secondary"

        with cols[idx]:
            if st.button(
                button_text,
                key=f"{answer_prefix}_btn_{question_id}_{idx}",
                use_container_width=True,
                type=button_type,
            ):
                st.session_state[f"{answer_prefix}_{question_id}"] = idx
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


render_topbar()
render_stepper()

topic = load_topic(st.session_state.topic_id) if st.session_state.topic_id else None

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

    with st.container():
        render_section_header(
            "Learn with Smart Tutor",
            "Read a lesson, test your understanding, and get a new explanation style if you need one.",
        )

        st.markdown(
            """
            <div class="smart-hero">
                <div class="smart-hero-title">Choose a topic</div>
                <div class="smart-hero-subtitle">
                    Select one topic to begin your guided learning flow.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        render_topic_cards(topics_with_titles)

        st.markdown("<br>", unsafe_allow_html=True)

        can_start = bool(st.session_state.get("topic_id"))
        if big_button("Start lesson", "start", disabled=not can_start, type="primary"):
            st.session_state.step = "lesson"
            reset_reexplain_state()
            st.rerun()


# -------------------------
# Lesson
# -------------------------
if st.session_state.step == "lesson":
    touch(st)

    with st.container():
        render_section_header(
            topic["title"],
            "Read this lesson before starting Quiz 1.",
        )

        st.markdown(
            "<div class='smart-helper'>Take your time. You’ll answer a short quiz next.</div>",
            unsafe_allow_html=True,
        )

        render_nav_buttons(back_step="select")

        st.markdown(
            "<div class='smart-bionic-toggle-label'>Reading Style</div>",
            unsafe_allow_html=True,
        )

        st.toggle(
            "Bionic Reading Mode",
            key="lesson_bionic",
        )

        if st.session_state.lesson_bionic:
            lesson_body = bionic_reading_html(topic["lesson"])
            lesson_html = f"""
            <div class='smart-lesson-markdown bionic'>
                <div class='lesson-content'>
                    {lesson_body}
                </div>
            </div>
            """
            st.markdown(lesson_html, unsafe_allow_html=True)
        else:
            lesson_html = f"""
            <div class='smart-lesson-markdown'>
                <div class='lesson-content'>
                    {topic["lesson"]}
                </div>
            </div>
            """
            st.markdown(lesson_html, unsafe_allow_html=True)

        if big_button("Start Quiz 1", "to_q1", type="primary"):
            st.session_state.step = "quiz1"
            st.rerun()

# -------------------------
# Quiz 1
# -------------------------
if st.session_state.step == "quiz1":
    touch(st)

    quiz = topic["quiz_1"]
    answers = {}

    with st.container():
        render_section_header(
            "Quiz 1",
            "Answer these questions based on the lesson.",
        )
        st.markdown(
            f"<div class='smart-helper'>{len(quiz['questions'])} questions</div>",
            unsafe_allow_html=True,
        )

        render_nav_buttons(back_step="lesson")

        for idx, q in enumerate(quiz["questions"], start=1):
            render_quiz_question(q, idx, "q1")

        for q in quiz["questions"]:
            selected = st.session_state.get(f"q1_{q['id']}", None)
            if selected is not None:
                answers[q["id"]] = selected

        unanswered = len(answers) < len(quiz["questions"])

        if unanswered:
            st.info("Answer all questions before continuing.")

        if big_button("Submit answers", "submit_q1", disabled=unanswered, type="primary"):
            st.session_state.q1_result = score_quiz(quiz, answers)
            incorrect = st.session_state.q1_result["incorrect_questions"]
            st.session_state.step = "quiz2" if not incorrect else "reexplain_q1"
            reset_reexplain_state()
            st.rerun()


# -------------------------
# Re-explain (after Quiz 1)
# -------------------------
if st.session_state.step == "reexplain_q1":
    touch(st)

    q1 = st.session_state.q1_result

    with st.container():
        render_section_header(
            "Let’s try a different explanation",
            "Choose the style that would help you understand this topic better.",
        )
        
        st.markdown(
            f"""
            <div class="smart-score-banner">
                <div class="smart-score-label">Quiz 1 result</div>
                <div class="smart-score-value">{q1['correct']} / {q1['total']}</div>
                <div class="smart-score-caption">
                    You answered {q1['correct']} out of {q1['total']} questions correctly.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        render_nav_buttons(back_step="quiz1")

        display_mode_buttons("pick_q1")
        selected_key = st.session_state.reexplain_mode

        custom_domain = None
        if selected_key and requires_input(selected_key):
            custom_domain = st.text_input(
                get_input_label(selected_key),
                placeholder="sports, cooking, retail, music...",
            )

        if not selected_key:
            st.info("Select an explanation style first.")

        generate_disabled = selected_key is None or (
            selected_key is not None
            and requires_input(selected_key)
            and not (custom_domain or "").strip()
        )

        if big_button(
            "Generate new explanation",
            "gen_q1",
            disabled=generate_disabled,
            type="primary",
        ):
            lesson = topic["lesson"]
            text, latency = generate_reexplanation(
                client, lesson, selected_key, custom_domain
            )
            st.session_state.reexplain_text = text
            st.session_state.reexplain_latency = latency

        if st.session_state.reexplain_text:
            latency_ms = st.session_state.reexplain_latency
            latency_text = (
                f"Generated locally in {latency_ms:.0f} ms"
                if latency_ms is not None
                else "Generated locally"
            )
            st.markdown(
                f"<div class='smart-helper'>{latency_text}</div>",
                unsafe_allow_html=True,
            )

            st.markdown("<div class='smart-output-box'>", unsafe_allow_html=True)
            st.markdown(
                "<div class='smart-output-title'>New explanation</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<div class='smart-output-text'>{st.session_state.reexplain_text}</div>",
                unsafe_allow_html=True,
            )
            st.markdown("</div>", unsafe_allow_html=True)

            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("Choose another style", key="change_style_q1", use_container_width=True):
                    st.session_state.reexplain_text = ""
                    st.session_state.reexplain_latency = None
                    st.rerun()

            with col_b:
                if st.button("Continue to Quiz 2", key="to_q2", type="primary", use_container_width=True):
                    reset_reexplain_state()
                    st.session_state.step = "quiz2"
                    st.rerun()


# -------------------------
# Quiz 2
# -------------------------
if st.session_state.step == "quiz2":
    touch(st)

    quiz = topic["quiz_2"]
    answers = {}

    with st.container():
        render_section_header(
            "Quiz 2",
            "Let’s check your understanding again.",
        )
        st.markdown(
            f"<div class='smart-helper'>{len(quiz['questions'])} questions</div>",
            unsafe_allow_html=True,
        )

        render_nav_buttons(back_step="reexplain_q1")

        for idx, q in enumerate(quiz["questions"], start=1):
            render_quiz_question(q, idx, "q2")

        for q in quiz["questions"]:
            selected = st.session_state.get(f"q2_{q['id']}", None)
            if selected is not None:
                answers[q["id"]] = selected

        unanswered = len(answers) < len(quiz["questions"])

        if unanswered:
            st.info("Answer all questions before continuing.")

        if big_button("Submit answers", "submit_q2", disabled=unanswered, type="primary"):
            st.session_state.q2_result = score_quiz(quiz, answers)
            st.session_state.step = "done"
            reset_reexplain_state()
            st.rerun()


# -------------------------
# Done
# -------------------------
if st.session_state.step == "done":
    touch(st)

    q1 = st.session_state.q1_result
    q2 = st.session_state.q2_result

    improved = q1 and (q2["correct"] > q1["correct"])

    with st.container():
        render_section_header(
            "Results",
            "Here’s how you did across both checks.",
        )

        render_nav_buttons(back_step="quiz2")

        if improved:
            st.markdown(
                f"""
                <div class="smart-result-hero">
                    <div class="smart-result-title">Nice progress</div>
                    <div class="smart-result-score">{q2['correct']} / {q2['total']}</div>
                    <div class="smart-result-subtitle">
                        The new explanation helped reinforce the topic.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
                <div class="smart-result-hero">
                    <div class="smart-result-title">Let’s try one more time</div>
                    <div class="smart-result-score">{q2['correct']} / {q2['total']}</div>
                    <div class="smart-result-subtitle">
                        A different explanation style may help clarify the topic.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(
                f"""
                <div class="smart-stat-card">
                    <div class="smart-stat-label">Quiz 1</div>
                    <div class="smart-stat-value">{q1['correct']} / {q1['total']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col2:
            st.markdown(
                f"""
                <div class="smart-stat-card">
                    <div class="smart-stat-label">Quiz 2</div>
                    <div class="smart-stat-value">{q2['correct']} / {q2['total']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        if q2["correct"] < q2["total"] - 1:
            st.warning("Try another explanation style before retrying.")

            display_mode_buttons("pick_done")
            selected_key = st.session_state.reexplain_mode

            custom_domain = None
            if selected_key and requires_input(selected_key):
                custom_domain = st.text_input(
                    get_input_label(selected_key),
                    placeholder="sports, cooking, retail, music...",
                    key="done_custom_domain",
                )

            if not selected_key:
                st.info("Select an explanation style first.")

            generate_disabled = selected_key is None or (
                selected_key is not None
                and requires_input(selected_key)
                and not (custom_domain or "").strip()
            )

            if big_button(
                "Generate re-explanation",
                "reexp",
                disabled=generate_disabled,
                type="primary",
            ):
                lesson = topic["lesson"]
                text, latency = generate_reexplanation(
                    client, lesson, selected_key, custom_domain
                )
                st.session_state.reexplain_text = text
                st.session_state.reexplain_latency = latency

            if st.session_state.reexplain_text:
                latency_ms = st.session_state.reexplain_latency
                latency_text = (
                    f"Generated locally in {latency_ms:.0f} ms"
                    if latency_ms is not None
                    else "Generated locally"
                )
                st.markdown(
                    f"<div class='smart-helper'>{latency_text}</div>",
                    unsafe_allow_html=True,
                )

                st.markdown("<div class='smart-output-box'>", unsafe_allow_html=True)
                st.markdown(
                    "<div class='smart-output-title'>New explanation</div>",
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f"<div class='smart-output-text'>{st.session_state.reexplain_text}</div>",
                    unsafe_allow_html=True,
                )
                st.markdown("</div>", unsafe_allow_html=True)

                if big_button("Try Quiz 1 again", "retry", type="primary"):
                    st.session_state.step = "quiz1"
                    reset_reexplain_state()
                    st.rerun()

        else:
            st.success("Great job!")

        st.markdown("<br>", unsafe_allow_html=True)

        col_a, col_b = st.columns(2)
        with col_a:
            if big_button("Back to topics", "reset_topics"):
                st.session_state.step = "select"
                reset_reexplain_state()
                st.rerun()
        with col_b:
            if big_button("Start over", "reset", type="primary"):
                st.session_state.step = "select"
                reset_reexplain_state()
                st.rerun()

render_footer()