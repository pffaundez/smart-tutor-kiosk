import streamlit as st
from app.ui.layout import open_main_card, close_main_card
from app.ui.components import result_hero, helper_text, stat_card

def render_results_screen():
    q1 = st.session_state.get("q1_result", {})
    q2 = st.session_state.get("q2_result", {})

    q1_correct = q1.get("correct", 0)
    q1_total = q1.get("total", 0)
    q2_correct = q2.get("correct", 0)
    q2_total = q2.get("total", 0)

    improved = q2_correct > q1_correct

    open_main_card("Results", "Here’s how you did across both checks.")

    if improved:
        result_hero(
            "Nice progress",
            f"{q2_correct}/{q2_total}",
            "The new explanation helped reinforce the topic."
        )
    else:
        result_hero(
            "Let’s try one more time",
            f"{q2_correct}/{q2_total}",
            "A different explanation style may help clarify the topic."
        )

    c1, c2 = st.columns(2)
    with c1:
        stat_card("Quiz 1", f"{q1_correct}/{q1_total}")
    with c2:
        stat_card("Quiz 2", f"{q2_correct}/{q2_total}")

    st.markdown("<br>", unsafe_allow_html=True)

    if improved:
        helper_text("You improved after the second explanation.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Review another topic"):
                _reset_for_new_topic()
                st.rerun()
        with col2:
            if st.button("Start again", type="primary"):
                _reset_current_topic()
                st.rerun()
    else:
        helper_text("Try another explanation style before retrying.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Choose another topic"):
                _reset_for_new_topic()
                st.rerun()
        with col2:
            if st.button("Try another explanation", type="primary"):
                st.session_state["step"] = "reexplain"
                st.rerun()

    close_main_card()

def _reset_current_topic():
    st.session_state["answers_q1"] = {}
    st.session_state["answers_q2"] = {}
    st.session_state["q1_result"] = None
    st.session_state["q2_result"] = None
    st.session_state["reexplain_text"] = ""
    st.session_state["show_generated_reexplain"] = False
    st.session_state["step"] = "lesson"

def _reset_for_new_topic():
    _reset_current_topic()
    st.session_state["topic_id"] = None
    st.session_state["step"] = "topic"