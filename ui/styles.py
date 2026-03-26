import streamlit as st

def inject_global_styles():
    st.markdown("""
    <style>
    .stApp {
        background: #f5f7fb;
    }

    .main .block-container {
        max-width: 1100px;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    .smart-topbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
        padding: 0.5rem 0 1rem 0;
    }

    .smart-brand {
        display: flex;
        flex-direction: column;
        gap: 0.15rem;
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
        padding: 0.3rem 0.7rem;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 600;
        background: #e5eefc;
        color: #1d4ed8;
    }

    .smart-stepper {
        display: grid;
        grid-template-columns: repeat(6, 1fr);
        gap: 0.75rem;
        margin: 1rem 0 1.5rem 0;
    }

    .smart-step {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 16px;
        padding: 0.85rem 0.75rem;
        text-align: center;
        font-size: 0.9rem;
        font-weight: 600;
        color: #6b7280;
    }

    .smart-step.active {
        border: 2px solid #2563eb;
        color: #111827;
        box-shadow: 0 6px 20px rgba(37, 99, 235, 0.10);
    }

    .smart-step.done {
        background: #eff6ff;
        border: 1px solid #bfdbfe;
        color: #1d4ed8;
    }

    .smart-main-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 24px;
        padding: 1.5rem;
        box-shadow: 0 8px 30px rgba(17, 24, 39, 0.05);
        margin-bottom: 1.5rem;
    }

    .smart-section-title {
        font-size: 1.6rem;
        font-weight: 750;
        color: #111827;
        margin-bottom: 0.35rem;
    }

    .smart-section-subtitle {
        font-size: 1rem;
        color: #6b7280;
        margin-bottom: 1.25rem;
    }

    .smart-helper {
        font-size: 0.95rem;
        color: #6b7280;
        margin-bottom: 1rem;
    }

    .smart-topic-card,
    .smart-mode-card,
    .smart-stat-card,
    .smart-result-card {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 18px;
        padding: 1rem;
        box-shadow: 0 4px 18px rgba(17, 24, 39, 0.04);
    }

    .smart-card-selected {
        border: 2px solid #2563eb !important;
        background: #f8fbff;
    }

    .smart-card-title {
        font-size: 1.05rem;
        font-weight: 700;
        color: #111827;
        margin-bottom: 0.25rem;
    }

    .smart-card-text {
        font-size: 0.95rem;
        color: #6b7280;
        line-height: 1.5;
    }

    .smart-quiz-label {
        font-size: 0.82rem;
        font-weight: 700;
        color: #2563eb;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-bottom: 0.4rem;
    }

    .smart-question-card {
        background: #fafafa;
        border: 1px solid #e5e7eb;
        border-radius: 18px;
        padding: 1rem;
        margin-bottom: 1rem;
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
        margin-bottom: 0.3rem;
    }

    .smart-result-score {
        font-size: 2rem;
        font-weight: 800;
        color: #1d4ed8;
        margin-bottom: 0.25rem;
    }

    .smart-footer {
        text-align: center;
        color: #9ca3af;
        font-size: 0.85rem;
        margin-top: 1rem;
    }

    div.stButton > button {
        width: 100%;
        border-radius: 14px;
        padding: 0.75rem 1rem;
        font-weight: 700;
        border: none;
    }

    div[data-testid="stHorizontalBlock"] > div {
        align-self: stretch;
    }
    </style>
    """, unsafe_allow_html=True)