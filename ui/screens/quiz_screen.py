import streamlit as st
from app.ui.layout import open_main_card, close_main_card
from app.ui.components import helper_text, question_label

def _render_quiz(title: str, subtitle: str, quiz_key: str, answers_key: str, next_step: str):
    quiz = st.session_state.get(quiz_key, [])

    open_main_card(title, subtitle)
    helper_text(f"{len(quiz)} questions")

    answers = st.session_state.get(answers_key, {})

    for i, q in enumerate(quiz):
        st.markdown('<div class="smart-question-card">', unsafe_allow_html=True)
        question_label(f"Question {i+1}")
        st.markdown(f"**{q['question']}**")

        selected = st.radio(
            label=f"q_{i}",
            options=q["options"],
            index=q["options"].index(answers[i]) if i in answers else None,
            key=f"{answers_key}_{i}",
            label_visibility="collapsed"
        )
        answers[i] = selected
        st.markdown("</div>", unsafe_allow_html=True)

    st.session_state[answers_key] = answers

    unanswered = len(answers) < len(quiz)

    if unanswered:
        helper_text("Answer all questions before continuing.")

    if st.button("Submit answers", disabled=unanswered, type="primary"):
        st.session_state["step"] = next_step
        st.rerun()

    close_main_card()

def render_quiz_1_screen():
    _render_quiz(
        "Quiz 1",
        "Answer these questions based on the lesson.",
        quiz_key="quiz_1",
        answers_key="answers_q1",
        next_step="reexplain"
    )

def render_quiz_2_screen():
    _render_quiz(
        "Quiz 2",
        "Let’s check your understanding again.",
        quiz_key="quiz_2",
        answers_key="answers_q2",
        next_step="results"
    )