import streamlit as st
from app.ui.layout import open_main_card, close_main_card
from app.ui.components import helper_text

def render_topic_screen():
    open_main_card(
        "",
        "Read a lesson, test your understanding, and get a new explanation style if you need one."
    )

    helper_text("Choose a topic to begin.")

    topics = st.session_state.get("topics", [])

    selected = st.session_state.get("topic_id")
    cols = st.columns(3)

    for idx, topic in enumerate(topics):
        with cols[idx % 3]:
            is_selected = selected == topic["id"]
            border = "2px solid #2563eb" if is_selected else "1px solid #e5e7eb"
            st.markdown(f"""
            <div style="
                background:white;
                border:{border};
                border-radius:18px;
                padding:1rem;
                min-height:150px;
                margin-bottom:0.75rem;
                box-shadow:0 4px 18px rgba(17,24,39,.04);
            ">
                <div style="font-size:1.05rem;font-weight:700;color:#111827;margin-bottom:.3rem;">
                    {topic["title"]}
                </div>
                <div style="font-size:.95rem;color:#6b7280;line-height:1.5;">
                    {topic.get("description", "Short topic introduction.")}
                </div>
            </div>
            """, unsafe_allow_html=True)

            if st.button(f"Select {topic['title']}", key=f"topic_{topic['id']}"):
                st.session_state["topic_id"] = topic["id"]
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    can_continue = bool(st.session_state.get("topic_id"))
    if st.button("Start lesson", disabled=not can_continue, type="primary"):
        st.session_state["step"] = "lesson"
        st.rerun()

    close_main_card()