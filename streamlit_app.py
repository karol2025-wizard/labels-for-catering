import streamlit as st

st.set_page_config(
    page_title="Labels for Catering",
    page_icon="🏷️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

ALLERGIES = [
    "Dairy",
    "Dairy & nuts",
    "Vegan & nuts",
    "Vegan & gluten",
    "Gluten, meat & dairy",
    "Gluten, meat & nuts",
    "Gluten & nuts",
    "Vegan",
]

CATEGORIES = [
    "Salades",
    "Mezzes",
    "Dips",
    "Plats Groupe",
    "Plats Individus",
]

if "screen" not in st.session_state:
    st.session_state.screen = "home"

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 2.5rem;
        max-width: 720px;
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
        margin: 0 0 28px;
    }
    div[class*="st-key-choice_"] button,
    div[class*="st-key-allergy_"] button,
    div[class*="st-key-category_"] button {
        width: 100%;
        background: #ffffff;
        color: #111827;
        border: 1px solid #d1d5db;
        border-radius: 2px;
        min-height: 92px;
        font-size: 20px;
        font-weight: 700;
        margin-bottom: 14px;
    }
    div[class*="st-key-choice_"] button:hover,
    div[class*="st-key-allergy_"] button:hover,
    div[class*="st-key-category_"] button:hover {
        border-color: #1E3A8A;
        color: #1E3A8A;
        background: #ffffff;
    }
    div.st-key-back button {
        background: transparent;
        border: none;
        color: #1E3A8A;
        font-weight: 600;
        padding-left: 0;
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


def show_menu(labels, key_prefix):
    for label in labels:
        st.button(label, key=f"{key_prefix}_{label}", use_container_width=True)


if st.session_state.screen == "home":
    if st.button("Allergies", key="choice_allergies", use_container_width=True):
        st.session_state.screen = "allergies"
        st.rerun()
    if st.button("Articles", key="choice_articles", use_container_width=True):
        st.session_state.screen = "articles"
        st.rerun()
else:
    if st.button("← Retour", key="back"):
        st.session_state.screen = "home"
        st.rerun()
    if st.session_state.screen == "allergies":
        show_menu(ALLERGIES, "allergy")
    else:
        show_menu(CATEGORIES, "category")
