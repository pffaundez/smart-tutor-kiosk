import streamlit as st

def helper_text(text: str):
    st.markdown(f'<div class="smart-helper">{text}</div>', unsafe_allow_html=True)

def info_badge(text: str):
    st.markdown(f'<span class="smart-badge">{text}</span>', unsafe_allow_html=True)

def topic_card(title: str, description: str, selected: bool = False):
    cls = "smart-topic-card smart-card-selected" if selected else "smart-topic-card"
    st.markdown(f"""
    <div class="{cls}">
        <div class="smart-card-title">{title}</div>
        <div class="smart-card-text">{description}</div>
    </div>
    """, unsafe_allow_html=True)

def mode_card(title: str, description: str, emoji: str = "✨", selected: bool = False):
    cls = "smart-mode-card smart-card-selected" if selected else "smart-mode-card"
    st.markdown(f"""
    <div class="{cls}">
        <div class="smart-card-title">{emoji} {title}</div>
        <div class="smart-card-text">{description}</div>
    </div>
    """, unsafe_allow_html=True)

def stat_card(label: str, value: str):
    st.markdown(f"""
    <div class="smart-stat-card">
        <div class="smart-card-text">{label}</div>
        <div class="smart-card-title">{value}</div>
    </div>
    """, unsafe_allow_html=True)

def result_hero(title: str, score_text: str, subtitle: str):
    st.markdown(f"""
    <div class="smart-result-hero">
        <div class="smart-result-title">{title}</div>
        <div class="smart-result-score">{score_text}</div>
        <div class="smart-card-text">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)

def question_label(text: str):
    st.markdown(f'<div class="smart-quiz-label">{text}</div>', unsafe_allow_html=True)