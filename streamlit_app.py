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

ITEMS = {
    "Salades": [
        "Classic Fattouch",
        "Zesty Fattouch",
        "Chou Frisé Kale",
    ],
    "Mezzes": [
        "Yalanji",
        "Kibbeh Pistaches",
        "Chou-Fleur",
    ],
    "Dips": [
        "Hummus",
        "Mouhammara",
        "Mutabbal Betteraves",
        "Mutabbal Aubergine",
        "Labneh",
        "Pain Saj",
    ],
    "Plats Groupe": [
        "Crispy Taouk Kit",
        "Saumon Kit",
        "Shawarma Agneau Kit",
        "Shish Taouk Kit",
        "Riz",
    ],
    "Plats Individus": [
        "Lamb Shawarma Plate",
        "Shish Taouk Plate",
        "Mix Plate — Shish Taouk + Lamb",
        "Salmon Plate",
        "Hummus Shawarma — Lamb",
    ],
    "Sandwiches": [
        "Crispy Taouk",
        "Shish Taouk",
        "Shawarma — Lamb",
        "Cauliflower",
        "Falafel",
        "Shawarma — Chicken",
        "Halloumi",
    ],
    "Dessert": [
        "Strawberry Almond Cookie",
        "Pistachio Baklava Cookie",
        "Date Cookie",
    ],
}

if "screen" not in st.session_state:
    st.session_state.screen = "home"
if "category" not in st.session_state:
    st.session_state.category = None

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
    div[class*="st-key-category_"] button,
    div[class*="st-key-item_"] button {
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
    div[class*="st-key-category_"] button:hover,
    div[class*="st-key-item_"] button:hover {
        border-color: #1E3A8A;
        color: #1E3A8A;
        background: #ffffff;
    }
    .category-title {
        text-align: center;
        color: #1E3A8A;
        font-size: 22px;
        font-weight: 700;
        margin: 4px 0 18px;
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
    for index, label in enumerate(labels):
        st.button(label, key=f"{key_prefix}_{index}", use_container_width=True)


if st.session_state.screen == "home":
    if st.button("Allergies", key="choice_allergies", use_container_width=True):
        st.session_state.screen = "allergies"
        st.rerun()
    if st.button("Articles", key="choice_articles", use_container_width=True):
        st.session_state.screen = "articles"
        st.rerun()
else:
    if st.button("← Retour", key="back"):
        if st.session_state.screen == "items":
            st.session_state.screen = "articles"
            st.session_state.category = None
        else:
            st.session_state.screen = "home"
        st.rerun()

    if st.session_state.screen == "allergies":
        show_menu(ALLERGIES, "allergy")
    elif st.session_state.screen == "articles":
        for index, category in enumerate(ITEMS):
            if st.button(category, key=f"category_{index}", use_container_width=True):
                st.session_state.category = category
                st.session_state.screen = "items"
                st.rerun()
    elif st.session_state.category in ITEMS:
        st.markdown(
            f'<p class="category-title">{st.session_state.category}</p>',
            unsafe_allow_html=True,
        )
        show_menu(ITEMS[st.session_state.category], "item")
