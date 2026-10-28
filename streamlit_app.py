import streamlit as st

st.set_page_config(
    page_title="Labels for Catering",
    page_icon="🏷️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 4rem;
    }
    .catering-header {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 16px;
        padding: 12px 0 4px;
    }
    .catering-logo {
        font-size: 52px;
        line-height: 1;
    }
    .catering-title {
        font-size: 44px;
        font-weight: 700;
        background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .catering-subtitle {
        text-align: center;
        color: #6B7280;
        font-size: 16px;
        margin: 0 0 8px;
    }
    </style>
    <div class="catering-header">
        <div class="catering-logo">🏷️🍽️</div>
        <h1 class="catering-title">Labels for Catering</h1>
    </div>
    <p class="catering-subtitle">Print labels for catering</p>
    """,
    unsafe_allow_html=True,
)
