from pathlib import Path

import streamlit as st

from app.core.content_loader import list_topics, load_topic
from app.core.reexplain_service import generate_reexplanation
from app.core.scoring import score_quiz
from app.core.session import init_session_state, maybe_reset, touch
from app.llm.client import LLMClient
from app.prompts.reexplain_modes import (
    get_input_label,
    get_label,
    get_mode_keys,
    requires_input,
)
from app.core.text_processor import markdown_bold_to_html

DEBUG_MODE = False

st.set_page_config(
    page_title="Learn with Smart Tutor Demo",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def load_css():
    """
    Load external CSS so styling stays separate from app logic.
    """
    css_path = Path(__file__).parent / "styles" / "main.css"
    with open(css_path, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


load_css()

init_session_state(st)

# Keep optional UI state explicit to avoid missing-key issues after reruns.
if "q1_result" not in st.session_state:
    st.session_state.q1_result = None

if "q2_result" not in st.session_state:
    st.session_state.q2_result = None

if "quiz_current_question" not in st.session_state:
    st.session_state.quiz_current_question = 0


llm3 = "qwen2.5:3b"

if DEBUG_MODE:
    with st.expander("LLM Settings", expanded=False):
        base_url = st.text_input("Base URL", value="http://127.0.0.1:11434")
        model_name = st.text_input("Model", value=llm3)
else:
    base_url = "http://127.0.0.1:11434"
    model_name = llm3

client = LLMClient(base_url=base_url, model=model_name)

MODE_UI = {
    "easy_to_read": {
        "label": "Easy-to-Read",
        "desc": "Clearer wording with simpler structure.",
        "emoji": "📘",
    },
    "simple": {
        "label": "Simple",
        "desc": "A shorter, more direct version.",
        "emoji": "✨",
    },
    "daily_analogies": {
        "label": "Examples",
        "desc": "Uses familiar real-world examples.",
        "emoji": "🔄",
    },
    "custom_domain_analogies": {
        "label": "Custom Analogies",
        "desc": "Connects the lesson to an area you choose.",
        "emoji": "🎯",
    },
}


def big_button(label, key, disabled=False, type="secondary"):
    """
    Create a standard full-width button used across screens.
    """
    return st.button(
        label,
        key=key,
        use_container_width=True,
        disabled=disabled,
        type=type,
    )


def reset_reexplain_state():
    """
    Clear generated explanation state before entering a new branch.
    """
    st.session_state.reexplain_text = ""
    st.session_state.reexplain_latency = None
    st.session_state.reexplain_mode = None


def reset_app_state():
    """
    Fully reset the app to the initial topic-selection state.
    """
    st.session_state.topic_id = None
    st.session_state.q1_result = None
    st.session_state.q2_result = None
    st.session_state.reexplain_text = ""
    st.session_state.reexplain_latency = None
    st.session_state.reexplain_mode = None
    st.session_state.step = "select"
    st.session_state.quiz_current_question = 0

    for key in list(st.session_state.keys()):
        if (
            key.startswith("q1_")
            or key.startswith("q2_")
            or key.startswith("pick_lesson_")
            or key.startswith("pick_review_")
            or key.startswith("pick_done_")
            or key.startswith("reading_mode_")
        ):
            del st.session_state[key]


def render_nav_buttons(back_step=None, back_label="Back", home_label="Home", include_test=False):
    """
    Keep navigation consistent across screens.
    """
    st.markdown("<div class='nav-button-row'>", unsafe_allow_html=True)

    if include_test:
        col1, col2, col3, col4 = st.columns([1, 3, 1, 0.5])
    else:
        col1, col2, col3, col4 = st.columns([1, 6, 1, 0.5])

    with col1:
        if st.button(
            back_label,
            key=f"back_{st.session_state.step}",
            disabled=back_step is None,
            use_container_width=True,
            type="secondary",
        ):
            if back_step is not None:
                st.session_state.step = back_step
                st.rerun()

    if include_test:
        with col2:
            if big_button("Test your understanding", "to_q1_sticky", type="primary"):
                reset_reexplain_state()
                st.session_state.step = "quiz1"
                st.rerun()

    with col3:
        if st.button(
            home_label,
            key=f"home_{st.session_state.step}",
            use_container_width=True,
            type="secondary",
        ):
            reset_app_state()
            st.rerun()

    with col4:
        if st.button(
            "🔄",
            key=f"reset_{st.session_state.step}",
            use_container_width=True,
            type="secondary",
            help="Reset session and return to home"
        ):
            reset_app_state()
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


def render_topbar():
    """
    Render project branding and main logo.
    """
    col1, col2 = st.columns([6, 1])

    with col1:
        st.markdown(
            """
            <div class="smart-brand">
                <div class="smart-title">🧠 Learn with Smart Tutor KI-osk 🦉</div>
                <div class="smart-subtitle">Interactive learning demo</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.image("app/assets/ki_owl.png", width=160)


def render_footer():
    """
    Keep branding in the footer without competing with the learning flow.
    """
    col_left, col_center, col_right = st.columns([2, 4, 2])

    with col_left:
        st.image("app/assets/dice.png", width=140)

    with col_center:
        st.markdown(
            "<div class='smart-footer'>Local-first tutoring experience</div>",
            unsafe_allow_html=True,
        )

    with col_right:
        pass


def render_section_header(title: str, subtitle: str | None = None):
    """
    Shared section header for all screens.
    """
    st.markdown(f"<div class='smart-section-title'>{title}</div>", unsafe_allow_html=True)
    if subtitle:
        st.markdown(
            f"<div class='smart-section-subtitle'>{subtitle}</div>",
            unsafe_allow_html=True,
        )


def get_mode_meta(mode_key: str):
    """
    Resolve UI metadata for explanation modes with a safe fallback.
    """
    fallback_label = get_label(mode_key)
    data = MODE_UI.get(
        mode_key,
        {"label": fallback_label, "desc": "", "emoji": "✨"},
    )
    return data["label"], data["desc"], data["emoji"]


def set_reexplain_mode(mode_key: str):
    """
    Selecting a new mode always clears the previous generated explanation.
    """
    st.session_state.reexplain_mode = mode_key
    st.session_state.reexplain_text = ""
    st.session_state.reexplain_latency = None


def render_mode_cards(prefix: str, helper_text: str):
    """
    Render explanation-style options as selectable cards.
    """
    mode_keys = get_mode_keys()
    cols = st.columns(len(mode_keys))

    st.markdown(
        f"<div class='smart-mode-help'>{helper_text}</div>",
        unsafe_allow_html=True,
    )

    for col, key in zip(cols, mode_keys):
        label, desc, emoji = get_mode_meta(key)
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
                set_reexplain_mode(key)
                st.rerun()


def recommend_mode(q_result):
    """
    Recommend a follow-up explanation style based on quiz performance.
    """
    if not q_result or not q_result.get("total"):
        return None

    score = q_result["correct"] / q_result["total"]

    if score < 0.5:
        return "easy_to_read"
    if score < 0.8:
        return "simple"
    return "daily_analogies"


def get_recommendation_copy(q_result):
    """
    Translate quiz performance into recommendation banner copy.
    """
    recommended = recommend_mode(q_result)
    if recommended == "easy_to_read":
        return (
            recommended,
            "Recommended for you",
            "You missed several questions. A clearer and simpler explanation may help.",
        )
    if recommended == "simple":
        return (
            recommended,
            "Recommended for you",
            "A shorter, more direct explanation may help reinforce the key ideas.",
        )
    if recommended == "daily_analogies":
        return (
            recommended,
            "Recommended for you",
            "You did well. An example-based explanation can help deepen understanding.",
        )
    return None, None, None


def render_recommendation_top(prefix: str, recommended_mode: str, title: str, text: str):
    """
    Show a top recommendation while still allowing all other explanation modes.
    """
    label, _desc, emoji = get_mode_meta(recommended_mode)
    selected = st.session_state.reexplain_mode == recommended_mode

    st.markdown(
        f"""
        <div class="smart-recommendation-banner">
            <div class="smart-recommendation-label">{title}</div>
            <div class="smart-recommendation-title">{emoji} {label}</div>
            <div class="smart-recommendation-text">{text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    button_label = f"Selected: {label}" if selected else f"Try {label}"
    if st.button(button_label, key=f"{prefix}_recommended_{recommended_mode}", use_container_width=True):
        set_reexplain_mode(recommended_mode)
        st.rerun()


def render_original_lesson_html(source_text: str, use_bionic: bool = False) -> str:
    """
    Reuse the same original lesson content in the comparison view.
    """
    if use_bionic:
        lesson_body = bionic_reading_html(source_text)
        return f"<div class='smart-compare-content'>{lesson_body}</div>"
    return f"<div class='smart-compare-content'>{source_text}</div>"


def render_compare_view(source_text: str, reexplain_text: str, use_bionic_original: bool = False):
    """
    Show original lesson and generated explanation side by side.
    """
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("<div class='smart-compare-header'>Original</div>", unsafe_allow_html=True)
        original_html = f"""
        <div class='smart-compare-card original'>
            <div class='smart-compare-title'>Lesson</div>
            {render_original_lesson_html(source_text, use_bionic=use_bionic_original)}
        </div>
        """
        st.markdown(original_html, unsafe_allow_html=True)

    with col_right:
        st.markdown("<div class='smart-compare-header'>New version</div>", unsafe_allow_html=True)
        rendered_reexplain = markdown_bold_to_html(reexplain_text)
        reexplain_html = f"""
        <div class='smart-compare-card reexplained'>
            <div class='smart-compare-title'>Re-explanation</div>
            <div class='smart-compare-content'>{rendered_reexplain}</div>
        </div>
        """
        st.markdown(reexplain_html, unsafe_allow_html=True)


def render_reexplanation_section(
    prefix: str,
    lesson_text: str,
    heading: str,
    helper_text: str,
    generate_label: str,
    recommended_mode: str | None = None,
    recommendation_title: str | None = None,
    recommendation_text: str | None = None,
    use_bionic_original: bool = False,
):
    """
    Handle explanation mode selection, generation, and side-by-side comparison.
    """
    render_section_header(heading, None)

    if recommended_mode and recommendation_title and recommendation_text:
        render_recommendation_top(
            prefix=prefix,
            recommended_mode=recommended_mode,
            title=recommendation_title,
            text=recommendation_text,
        )
        st.markdown(
            "<div class='smart-mode-help'>You can also choose any other explanation style below.</div>",
            unsafe_allow_html=True,
        )

    render_mode_cards(prefix, helper_text)
    selected_key = st.session_state.reexplain_mode

    custom_domain = None
    if selected_key and requires_input(selected_key):
        custom_domain = st.text_input(
            get_input_label(selected_key),
            placeholder="sports, cooking, retail, music...",
            key=f"{prefix}_custom_domain",
        )

    if not selected_key:
        st.info("Choose an explanation style to continue.")

    generate_disabled = selected_key is None or (
        selected_key is not None
        and requires_input(selected_key)
        and not (custom_domain or "").strip()
    )

    if big_button(generate_label, f"{prefix}_generate", disabled=generate_disabled, type="primary"):
        loader_placeholder = st.empty()

        with loader_placeholder.container():
            st.markdown(
                """
                <div class="smart-loader">
                    <div class="smart-loader-dots">
                        <div class="smart-loader-dot"></div>
                        <div class="smart-loader-dot"></div>
                        <div class="smart-loader-dot"></div>
                    </div>
                    <div class="smart-loader-text-wrap">
                        <div class="smart-loader-text">Generating explanation...</div>
                        <div class="smart-loader-subtext">This may take a few seconds.</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        text, latency = generate_reexplanation(
            client,
            lesson_text,
            selected_key,
            custom_domain,
        )

        loader_placeholder.empty()

        st.session_state.reexplain_text = text
        st.session_state.reexplain_latency = latency
        st.rerun()

    if st.session_state.reexplain_text:
        latency_ms = st.session_state.reexplain_latency
        latency_text = (
            f"Generated locally in {latency_ms:.0f} ms"
            if latency_ms is not None
            else "Generated locally"
        )
        st.markdown(
            f"<div class='smart-compare-latency'>{latency_text}</div>",
            unsafe_allow_html=True,
        )

        render_compare_view(
            source_text=lesson_text,
            reexplain_text=st.session_state.reexplain_text,
            use_bionic_original=use_bionic_original,
        )


def render_topic_cards(topics_with_titles):
    """
    Render topic cards plus a non-interactive preview for future topic generation.
    """
    topic_items = list(topics_with_titles.items())

    total_cards = len(topic_items) + 1
    n_cols = min(3, max(1, total_cards))
    cols = st.columns(n_cols)

    for idx, (title, tid) in enumerate(topic_items):
        topic_data = load_topic(tid)
        description = (
            topic_data.get("description")
            or topic_data.get("summary")
            or "Short topic introduction."
        )

        with cols[idx % n_cols]:
            st.markdown(
                f"""
                <div class="smart-grid-card">
                    <div class="smart-card-title">{title}</div>
                    <div class="smart-card-text">{description}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.button(f"Choose {title}", key=f"topic_{tid}", use_container_width=True):
                st.session_state.topic_id = tid
                st.session_state.q1_result = None
                st.session_state.q2_result = None
                st.session_state.step = "lesson"
                reset_reexplain_state()
                st.rerun()

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
    """
    Render one quiz question with 2x2 answer grid (like "Quien quiere ser millonario").
    """
    question_id = question["id"]
    options = question["options"]
    option_letters = ["A", "B", "C", "D", "E", "F"]

    selected_value = st.session_state.get(f"{answer_prefix}_{question_id}", None)

    st.markdown(
        f"<div class='smart-question-label'>Question {question_number}</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div class='smart-question-text'>{question['question']}</div>",
        unsafe_allow_html=True,
    )

    # Create 2x2 grid for answers
    st.markdown('<div class="smart-quiz-grid">', unsafe_allow_html=True)
    
    for row in range(2):
        col1, col2 = st.columns(2)
        cols = [col1, col2]
        
        for col_idx in range(2):
            option_idx = row * 2 + col_idx
            
            if option_idx < len(options):
                option = options[option_idx]
                letter = option_letters[option_idx]
                button_text = f"{letter}. {option}"
                button_type = "primary" if selected_value == option_idx else "secondary"
                
                with cols[col_idx]:
                    if st.button(
                        button_text,
                        key=f"{answer_prefix}_btn_{question_id}_{option_idx}",
                        use_container_width=True,
                        type=button_type,
                    ):
                        st.session_state[f"{answer_prefix}_{question_id}"] = option_idx
                        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown('<div class="smart-question-divider"></div>', unsafe_allow_html=True)


def render_quiz_carousel(quiz, answer_prefix: str):
    """
    Render quiz questions in a carousel view (one question at a time).
    """
    questions = quiz["questions"]
    total_questions = len(questions)
    current_question_idx = st.session_state.quiz_current_question
    
    # Clamp to valid range
    current_question_idx = max(0, min(current_question_idx, total_questions - 1))
    
    question = questions[current_question_idx]
    
    # Render current question
    render_quiz_question(question, current_question_idx + 1, answer_prefix)
    
    # Navigation controls
    st.markdown('<div class="smart-quiz-carousel-nav">', unsafe_allow_html=True)
    
    col_prev, col_counter, col_next = st.columns([1, 2, 1])
    
    with col_prev:
        if st.button("← Previous", use_container_width=True, disabled=current_question_idx == 0):
            st.session_state.quiz_current_question = current_question_idx - 1
            st.rerun()
    
    with col_counter:
        st.markdown(
            f"<div style='text-align: center; padding: 0.5rem; font-weight: 600; color: #374151;'>"
            f"{current_question_idx + 1} / {total_questions}"
            f"</div>",
            unsafe_allow_html=True,
        )
    
    with col_next:
        if st.button("Next →", use_container_width=True, disabled=current_question_idx == total_questions - 1):
            st.session_state.quiz_current_question = current_question_idx + 1
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)


render_topbar()

topic = load_topic(st.session_state.topic_id) if st.session_state.topic_id else None

# Topic selection screen
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

# Lesson screen
# Re-explanation is intentionally available before the first quiz to reduce friction.
if st.session_state.step == "lesson" and topic:
    touch(st)

    with st.container():
        render_section_header(
            topic["title"],
            "Read the lesson, then explore another explanation style if you want.",
        )


        render_nav_buttons(back_step="select", include_test=True)

        if not st.session_state.reexplain_text:
            lesson_html = f"""
            <div class='smart-lesson-single-card'>
                <div class='smart-lesson-single-title'>Lesson</div>
                <div class='smart-lesson-markdown'>
                    <div class='lesson-content'>
                        {topic["lesson"]}
                    </div>
                </div>
            </div>
            """
            st.markdown(lesson_html, unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

        render_reexplanation_section(
            prefix="pick_lesson",
            lesson_text=topic["lesson"],
            heading="Want to understand this differently?",
            helper_text="Choose any explanation style below.",
            generate_label="Generate explanation",
            use_bionic_original=False,
        )

        st.markdown("<br>", unsafe_allow_html=True)


# Quiz 1: primary knowledge check after lesson
if st.session_state.step == "quiz1" and topic:
    touch(st)

    quiz = topic["quiz_1"]
    answers = {}

    with st.container():
        render_section_header(
            "Quiz 1",
            "Answer each question. You can navigate freely.",
        )
        st.markdown(
            f"<div class='smart-helper'>{len(quiz['questions'])} questions</div>",
            unsafe_allow_html=True,
        )

        render_nav_buttons(back_step="lesson")

        render_quiz_carousel(quiz, "q1")

        for q in quiz["questions"]:
            selected = st.session_state.get(f"q1_{q['id']}", None)
            if selected is not None:
                answers[q["id"]] = selected

        unanswered = len(answers) < len(quiz["questions"])

        if unanswered:
            st.info("Answer all questions before continuing.")

        if big_button("Submit answers", "submit_q1", disabled=unanswered, type="primary"):
            st.session_state.q1_result = score_quiz(quiz, answers)
            st.session_state.quiz_current_question = 0
            reset_reexplain_state()
            st.session_state.step = "quiz1_review"
            st.rerun()

# Quiz 1 review plus recommended re-explanation
if st.session_state.step == "quiz1_review" and topic:
    touch(st)

    q1 = st.session_state.q1_result
    recommended_mode, rec_title, rec_text = get_recommendation_copy(q1)

    with st.container():
        render_section_header(
            "Quiz 1 complete",
            "You can continue now or try another explanation first.",
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

        render_reexplanation_section(
            prefix="pick_review",
            lesson_text=topic["lesson"],
            heading="Try another explanation",
            helper_text="Choose any explanation style below.",
            generate_label="Generate explanation",
            recommended_mode=recommended_mode,
            recommendation_title=rec_title,
            recommendation_text=rec_text,
            use_bionic_original=False,
        )

        st.markdown("<br>", unsafe_allow_html=True)

        col_a, col_b = st.columns(2)
        with col_a:
            if big_button("Take backup quiz", "review_to_q2", type="primary"):
                reset_reexplain_state()
                st.session_state.step = "quiz2"
                st.rerun()
        with col_b:
            if big_button("Finish here", "review_to_done"):
                reset_reexplain_state()
                st.session_state.q2_result = None
                st.session_state.step = "done"
                st.rerun()

# Quiz 2: optional reinforcement quiz
if st.session_state.step == "quiz2" and topic:
    touch(st)

    quiz = topic["quiz_2"]
    answers = {}

    with st.container():
        render_section_header(
            "Quiz 2",
            "Backup quiz: check your understanding one more time.",
        )
        st.markdown(
            f"<div class='smart-helper'>{len(quiz['questions'])} questions</div>",
            unsafe_allow_html=True,
        )

        render_nav_buttons(back_step="quiz1_review")

        render_quiz_carousel(quiz, "q2")

        for q in quiz["questions"]:
            selected = st.session_state.get(f"q2_{q['id']}", None)
            if selected is not None:
                answers[q["id"]] = selected

        unanswered = len(answers) < len(quiz["questions"])

        if unanswered:
            st.info("Answer all questions before continuing.")

        if big_button("Submit answers", "submit_q2", disabled=unanswered, type="primary"):
            st.session_state.q2_result = score_quiz(quiz, answers)
            st.session_state.quiz_current_question = 0
            reset_reexplain_state()
            st.session_state.step = "done"
            st.rerun()

# Results screen
if st.session_state.step == "done" and topic:
    touch(st)

    q1 = st.session_state.q1_result
    q2 = st.session_state.q2_result
    improved = q1 and q2 and (q2["correct"] > q1["correct"])

    with st.container():
        render_section_header(
            "Results",
            "Here’s how you did across this session.",
        )

        render_nav_buttons(back_step="quiz1_review" if q2 is None else "quiz2")

        if q2 is None:
            st.markdown(
                f"""
                <div class="smart-result-hero">
                    <div class="smart-result-title">Session complete</div>
                    <div class="smart-result-score">{q1['correct']} / {q1['total']}</div>
                    <div class="smart-result-subtitle">
                        You completed the main quiz. The backup quiz was optional and was skipped.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        elif improved:
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
                    <div class="smart-result-title">Session complete</div>
                    <div class="smart-result-score">{q2['correct']} / {q2['total']}</div>
                    <div class="smart-result-subtitle">
                        You completed the backup quiz after exploring the topic.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        if q1:
            if q2 is None:
                st.markdown(
                    f"""
                    <div class="smart-stat-card">
                        <div class="smart-stat-label">Quiz 1</div>
                        <div class="smart-stat-value">{q1['correct']} / {q1['total']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
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