import streamlit as st
from app.ui.layout import open_main_card, close_main_card
from app.ui.components import helper_text

def render_lesson_screen():
    topic = st.session_state.get("current_topic", {})
    title = topic.get("title", "Lesson")

    open_main_card(title, "Read this lesson before starting Quiz 1.")
    helper_text("Take your time. You’ll answer a short quiz next.")

    lesson_md = topic.get("lesson", "")
    st.markdown(lesson_md)

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Back to topics"):
            st.session_state["step"] = "topic"
            st.rerun()

    with col2:
        if st.button("Start Quiz 1", type="primary"):
            st.session_state["step"] = "quiz_1"
            st.rerun()

    close_main_card()