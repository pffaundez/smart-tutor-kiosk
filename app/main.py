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

        h1, h2, h3 {
            color: #111827;
        }

        .smart-topbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 1rem;
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
            color: #111827;
        }

        .smart-subtitle {
            font-size: 0.95rem;
            color: #6b7280;
        }

        .smart-badge {
            display: inline-block;
            padding: 0.35rem 0.8rem;
            border-radius: 999px;
            font-size: 0.82rem;
            font-weight: 700;
            background: #e5eefc;
            color: #1d4ed8;
            white-space: nowrap;
        }

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
            color: #6b7280;
            box-shadow: 0 4px 18px rgba(17, 24, 39, 0.04);
        }

        .smart-step.active {
            border: 2px solid #2563eb;
            color: #111827;
            background: #f8fbff;
            box-shadow: 0 8px 22px rgba(37, 99, 235, 0.10);
        }

        .smart-step.done {
            background: #eff6ff;
            border: 1px solid #bfdbfe;
            color: #1d4ed8;
        }

        .smart-main-card {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 24px;
            padding: 1.5rem;
            box-shadow: 0 8px 30px rgba(17, 24, 39, 0.05);
            margin-bottom: 1.25rem;
        }

        .smart-main-card p {
            font-size: 1.18rem;
            line-height: 1.9;
            max-width: 760px;
            margin-left: auto;
            margin-right: auto;
            color: #111827;
        }

        .smart-section-title {
            font-size: 1.65rem;
            font-weight: 800;
            color: #111827;
            margin-bottom: 0.3rem;
        }

        .smart-section-subtitle {
            font-size: 1rem;
            color: #6b7280;
            margin-bottom: 1.25rem;
        }

        .smart-helper {
            font-size: 0.96rem;
            color: #6b7280;
            margin-bottom: 1rem;
        }

        .smart-hero {
            text-align: center;
            padding: 0.5rem 0 0.75rem 0;
        }

        .smart-hero-title {
            font-size: 2.2rem;
            font-weight: 800;
            color: #111827;
            margin-bottom: 0.35rem;
        }

        .smart-hero-subtitle {
            font-size: 1.05rem;
            color: #6b7280;
            max-width: 760px;
            margin: 0 auto;
            line-height: 1.6;
        }

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
            color: #111827;
            margin-bottom: 0.25rem;
        }

        .smart-card-text {
            font-size: 0.96rem;
            color: #6b7280;
            line-height: 1.5;
        }

        .smart-lesson-box {
            font-size: 1.18rem;
            line-height: 1.9;
            color: #111827;
            max-width: 760px;
            margin: 0 auto;
        }

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
            color: #2563eb;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-bottom: 0.45rem;
        }

        .smart-mode-help {
            text-align: left;
            margin-top: 0.2rem;
            margin-bottom: 1rem;
            font-size: 0.98rem;
            color: #6b7280;
        }

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
            color: #111827;
            margin-bottom: 0.25rem;
        }

        .smart-result-score {
            font-size: 2rem;
            font-weight: 800;
            color: #1d4ed8;
            margin-bottom: 0.25rem;
        }

        .smart-result-subtitle {
            font-size: 1rem;
            color: #6b7280;
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
            color: #6b7280;
            margin-bottom: 0.25rem;
        }

        .smart-stat-value {
            font-size: 1.35rem;
            font-weight: 800;
            color: #111827;
        }

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
            color: #111827;
            margin-bottom: 0.6rem;
        }

        .smart-output-text {
            font-size: 1.2rem;
            line-height: 1.95;
            color: #111827;
            max-width: 760px;
            margin: 0 auto;
        }

        .smart-footer {
            text-align: center;
            color: #9ca3af;
            font-size: 0.86rem;
            margin-top: 1rem;
        }

        div.stButton > button {
            width: 100%;
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

        div[data-testid="stHorizontalBlock"] > div {
            align-self: stretch;
        }

        /* NAV BUTTONS (Back / Home) */
        div.stButton > button[kind="secondary"] {
            background-color: #ffffff;
            color: #6b7280;
            border: 1px solid #e5e7eb;
            box-shadow: none;
            min-height: 2.6rem;
            font-weight: 600;
        }

        div.stButton > button[kind="secondary"]:hover {
            background-color: #f9fafb;
            border-color: #d1d5db;
            color: #374151;
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
            type="secondary",
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
        st.image("app/assets/ki_owl.png", use_container_width=True)


def render_footer():
    col1, col2 = st.columns([5, 2])

    with col1:
        st.markdown(
            "<div class='smart-footer'>Local-first tutoring experience</div>",
            unsafe_allow_html=True,
        )

    with col2:
        st.image("app/assets/bundes.png", width=300)


def open_main_card(title: str, subtitle: str | None = None):
    st.markdown('<div class="smart-main-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="smart-section-title">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(
            f'<div class="smart-section-subtitle">{subtitle}</div>',
            unsafe_allow_html=True,
        )


def close_main_card():
    st.markdown("</div>", unsafe_allow_html=True)


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
    st.markdown('<div class="mode-buttons">', unsafe_allow_html=True)

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

    st.markdown("</div>", unsafe_allow_html=True)


def render_topic_cards(topics_with_titles: dict[str, str]):
    selected_topic_id = st.session_state.get("topic_id")
    topic_items = list(topics_with_titles.items())
    cols = st.columns(min(3, max(1, len(topic_items))))

    for idx, (title, tid) in enumerate(topic_items):
        topic_data = load_topic(tid)
        description = topic_data.get("description") or topic_data.get("summary") or "Short topic introduction."
        selected = selected_topic_id == tid

        with cols[idx % len(cols)]:
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

    open_main_card(
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

    close_main_card()


# -------------------------
# Lesson
# -------------------------
if st.session_state.step == "lesson":
    touch(st)

    open_main_card(
        topic["title"],
        "Read this lesson before starting Quiz 1.",
    )

    st.markdown(
        "<div class='smart-helper'>Take your time. You’ll answer a short quiz next.</div>",
        unsafe_allow_html=True,
    )

    render_nav_buttons(back_step="select")
    
    st.markdown(f"<div class='smart-lesson-box'>{topic['lesson']}</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if big_button("Back to topics", "back_to_topics"):
            st.session_state.step = "select"
            st.rerun()
    with col2:
        if big_button("Start Quiz 1", "to_q1", type="primary"):
            st.session_state.step = "quiz1"
            st.rerun()

    close_main_card()


# -------------------------
# Quiz 1
# -------------------------
if st.session_state.step == "quiz1":
    touch(st)

    quiz = topic["quiz_1"]
    answers = {}

    open_main_card(
        "Quiz 1",
        "Answer these questions based on the lesson.",
    )
    st.markdown(
        f"<div class='smart-helper'>{len(quiz['questions'])} questions</div>",
        unsafe_allow_html=True,
    )

    render_nav_buttons(back_step="lesson")

    for idx, q in enumerate(quiz["questions"], start=1):
        st.markdown('<div class="smart-question-card">', unsafe_allow_html=True)
        st.markdown(
            f"<div class='smart-question-label'>Question {idx}</div>",
            unsafe_allow_html=True,
        )
        st.write(f"**{q['question']}**")
        choice = st.radio(
            "",
            range(len(q["options"])),
            format_func=lambda i, opts=q["options"]: opts[i],
            key=f"q1_{q['id']}",
        )
        answers[q["id"]] = choice
        st.markdown("</div>", unsafe_allow_html=True)

    if big_button("Submit answers", "submit_q1", type="primary"):
        st.session_state.q1_result = score_quiz(quiz, answers)
        incorrect = st.session_state.q1_result["incorrect_questions"]
        st.session_state.step = "quiz2" if not incorrect else "reexplain_q1"
        reset_reexplain_state()
        st.rerun()

    close_main_card()


# -------------------------
# Re-explain (after Quiz 1)
# -------------------------
if st.session_state.step == "reexplain_q1":
    touch(st)

    q1 = st.session_state.q1_result

    open_main_card(
        "Let’s try a different explanation",
        "Choose the style that would help you understand this topic better.",
    )

    st.markdown(
        f"""
        <div class="smart-helper">
            You got <strong>{q1['correct']} / {q1['total']}</strong> correct in Quiz 1.
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

    if big_button("Generate new explanation", "gen_q1", disabled=generate_disabled, type="primary"):
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
        st.markdown("<div class='smart-output-title'>New explanation</div>", unsafe_allow_html=True)
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

    close_main_card()


# -------------------------
# Quiz 2
# -------------------------
if st.session_state.step == "quiz2":
    touch(st)

    quiz = topic["quiz_2"]
    answers = {}

    open_main_card(
        "Quiz 2",
        "Let’s check your understanding again.",
    )
    st.markdown(
        f"<div class='smart-helper'>{len(quiz['questions'])} questions</div>",
        unsafe_allow_html=True,
    )

    render_nav_buttons(back_step="reexplain_q1")

    for idx, q in enumerate(quiz["questions"], start=1):
        st.markdown('<div class="smart-question-card">', unsafe_allow_html=True)
        st.markdown(
            f"<div class='smart-question-label'>Question {idx}</div>",
            unsafe_allow_html=True,
        )
        st.write(f"**{q['question']}**")
        choice = st.radio(
            "",
            range(len(q["options"])),
            format_func=lambda i, opts=q["options"]: opts[i],
            key=f"q2_{q['id']}",
        )
        answers[q["id"]] = choice
        st.markdown("</div>", unsafe_allow_html=True)

    if big_button("Submit answers", "submit_q2", type="primary"):
        st.session_state.q2_result = score_quiz(quiz, answers)
        st.session_state.step = "done"
        reset_reexplain_state()
        st.rerun()

    close_main_card()


# -------------------------
# Done
# -------------------------
if st.session_state.step == "done":
    touch(st)

    q1 = st.session_state.q1_result
    q2 = st.session_state.q2_result

    improved = q1 and (q2["correct"] > q1["correct"])

    open_main_card(
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

        if big_button("Generate re-explanation", "reexp", disabled=generate_disabled, type="primary"):
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
            st.markdown("<div class='smart-output-title'>New explanation</div>", unsafe_allow_html=True)
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

    close_main_card()

render_footer()