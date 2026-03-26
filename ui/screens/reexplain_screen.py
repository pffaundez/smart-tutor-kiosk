import streamlit as st
from app.ui.layout import open_main_card, close_main_card
from app.ui.components import helper_text

MODE_META = {
    "easy": {
        "label": "Easy-to-Read",
        "desc": "Clearer wording with simpler structure.",
        "emoji": "📘",
    },
    "simple": {
        "label": "Simple",
        "desc": "A shorter, more direct version.",
        "emoji": "✨",
    },
    "analogies": {
        "label": "Everyday Analogies",
        "desc": "Uses familiar real-world examples.",
        "emoji": "🔄",
    },
    "custom_domain": {
        "label": "Custom Domain",
        "desc": "Connects the lesson to an area you choose.",
        "emoji": "🎯",
    },
}

def render_reexplain_screen():
    open_main_card(
        "Let’s try a different explanation",
        "Choose the style that would help you understand this topic better."
    )

    helper_text("Choose one explanation option.")

    selected_mode = st.session_state.get("reexplain_mode")
    cols = st.columns(2)

    mode_keys = list(MODE_META.keys())
    for idx, mode_key in enumerate(mode_keys):
        mode = MODE_META[mode_key]
        selected = selected_mode == mode_key

        with cols[idx % 2]:
            css_class = "smart-mode-card smart-card-selected" if selected else "smart-mode-card"
            st.markdown(f"""
            <div class="{css_class}">
                <div class="smart-card-title">{mode['emoji']} {mode['label']}</div>
                <div class="smart-card-text">{mode['desc']}</div>
            </div>
            """, unsafe_allow_html=True)

            if st.button(f"Choose {mode['label']}", key=f"mode_{mode_key}"):
                st.session_state["reexplain_mode"] = mode_key
                st.rerun()

    requires_input = selected_mode == "custom_domain"
    custom_domain = st.session_state.get("custom_domain", "")

    if requires_input:
        custom_domain = st.text_input(
            "Choose a domain or interest area",
            value=custom_domain,
            placeholder="sports, cooking, retail, music..."
        )
        st.session_state["custom_domain"] = custom_domain

    st.markdown("<br>", unsafe_allow_html=True)

    can_generate = bool(selected_mode) and (not requires_input or bool(custom_domain.strip()))

    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("Back"):
            st.session_state["step"] = "quiz_1"
            st.rerun()

    with col2:
        if st.button("Generate new explanation", disabled=not can_generate, type="primary"):
            with st.spinner("Creating a new explanation..."):
                # Acá conectás tu servicio real
                # text, latency = generate_reexplanation(...)
                text = "Generated explanation goes here."
                latency = 15.8

            st.session_state["reexplain_text"] = text
            st.session_state["reexplain_latency"] = latency
            st.session_state["show_generated_reexplain"] = True
            st.rerun()

    if st.session_state.get("show_generated_reexplain") and st.session_state.get("reexplain_text"):
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("### New explanation")
        st.markdown(st.session_state["reexplain_text"])

        latency = st.session_state.get("reexplain_latency")
        if latency:
            helper_text(f"Generated locally in {latency:.1f}s")

        col3, col4 = st.columns([1, 1])
        with col3:
            if st.button("Choose another style"):
                st.session_state["show_generated_reexplain"] = False
                st.rerun()
        with col4:
            if st.button("Continue to Quiz 2", type="primary"):
                st.session_state["step"] = "quiz_2"
                st.rerun()

    close_main_card()