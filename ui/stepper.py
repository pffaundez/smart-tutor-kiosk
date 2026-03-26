import streamlit as st

STEP_ORDER = ["topic", "lesson", "quiz_1", "reexplain", "quiz_2", "results"]

STEP_LABELS = {
    "topic": "Topic",
    "lesson": "Lesson",
    "quiz_1": "Quiz 1",
    "reexplain": "Re-explain",
    "quiz_2": "Quiz 2",
    "results": "Results",
}

def render_stepper(current_step: str):
    current_index = STEP_ORDER.index(current_step)

    html = ['<div class="smart-stepper">']
    for idx, step in enumerate(STEP_ORDER):
        css_class = "smart-step"
        if idx < current_index:
            css_class += " done"
        elif idx == current_index:
            css_class += " active"
        html.append(f'<div class="{css_class}">{STEP_LABELS[step]}</div>')
    html.append('</div>')

    st.markdown("".join(html), unsafe_allow_html=True)