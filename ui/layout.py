import streamlit as st

def render_topbar():
    st.markdown("""
    <div class="smart-topbar">
        <div class="smart-brand">
            <div class="smart-title">Smart Tutor</div>
            <div class="smart-subtitle">Interactive learning demo</div>
        </div>
        <div class="smart-badge">Local AI</div>
    </div>
    """, unsafe_allow_html=True)

def open_main_card(title: str, subtitle: str | None = None):
    st.markdown('<div class="smart-main-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="smart-section-title">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="smart-section-subtitle">{subtitle}</div>', unsafe_allow_html=True)

def close_main_card():
    st.markdown('</div>', unsafe_allow_html=True)

def render_footer(latency_text: str | None = None):
    footer = "Local-first tutoring experience"
    if latency_text:
        footer += f" · {latency_text}"
    st.markdown(f'<div class="smart-footer">{footer}</div>', unsafe_allow_html=True)