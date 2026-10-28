import html

import streamlit as st

st.set_page_config(
    page_title="Labels for Catering",
    page_icon="✦",
    layout="centered",
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

STAR_COLORS = {
    "Salades": "#C6A45A",
    "Mezzes": "#6EAFC0",
    "Dips": "#2C6E78",
    "Plats Groupe": "#17233A",
    "Plats Individus": "#6E8EAE",
    "Sandwiches": "#8D6B3F",
    "Dessert": "#C6A45A",
}

NAVY = "#17233A"
TEAL = "#6EAFC0"


def burst(color: str, size: int = 78) -> str:
    petals = []
    for angle in (0, 45, 90, 135):
        petals.append(
            f'<ellipse cx="50" cy="50" rx="15" ry="40" fill="{color}" '
            f'transform="rotate({angle} 50 50)"/>'
        )
    return (
        f'<svg class="burst" width="{size}" height="{size}" viewBox="0 0 100 100" '
        f'aria-hidden="true">{"".join(petals)}</svg>'
    )


def sticker_name_html(name: str) -> tuple[str, str]:
    if " — " in name:
        main, detail = name.split(" — ", 1)
        body = (
            f"{html.escape(main)}"
            f'<span class="sticker-detail">{html.escape(detail)}</span>'
        )
        return body, "name-short"
    length = len(name)
    if length > 28:
        size = "name-long"
    elif length > 18:
        size = "name-medium"
    else:
        size = "name-short"
    return html.escape(name), size


def sticker_html(name: str, kicker: str, color: str) -> str:
    body, size = sticker_name_html(name)
    return f"""
    <div class="sticker-wrap">
      <div class="sticker">
        {burst(color, 72)}
        <div class="sticker-kicker">{html.escape(kicker)}</div>
        <div class="sticker-name {size}">{body}</div>
        <div class="sticker-rule"></div>
      </div>
    </div>
    """


if "screen" not in st.session_state:
    st.session_state.screen = "home"
if "category" not in st.session_state:
    st.session_state.category = None
if "sticker_name" not in st.session_state:
    st.session_state.sticker_name = None
if "sticker_from" not in st.session_state:
    st.session_state.sticker_from = None

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700&display=swap');

    html, body, [class*="css"], .stApp, .stMarkdown, button, p, h1 {
        font-family: Outfit, "Segoe UI", sans-serif;
    }
    .stApp {
        background: #E4DFD3;
    }
    header[data-testid="stHeader"] {
        background: transparent;
    }
    .block-container {
        padding-top: 2.2rem;
        max-width: 680px;
    }
    .brand {
        display: flex;
        align-items: center;
        gap: 16px;
        margin: 8px 0 28px;
    }
    .brand-kicker {
        margin: 0;
        color: #C6A45A;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 0.22em;
        text-transform: uppercase;
    }
    .brand h1 {
        margin: 2px 0 0;
        color: #17233A;
        font-size: 48px;
        line-height: 0.95;
        font-weight: 700;
        letter-spacing: -0.04em;
    }
    div[class*="st-key-choice_"] button,
    div[class*="st-key-allergy_"] button,
    div[class*="st-key-category_"] button,
    div[class*="st-key-item_"] button {
        width: 100%;
        background: transparent;
        color: #17233A;
        border: none;
        border-bottom: 1px solid rgba(23, 35, 58, 0.18);
        border-radius: 0;
        min-height: 74px;
        font-size: 22px;
        font-weight: 600;
        text-align: left;
        padding-left: 4px;
        justify-content: flex-start;
    }
    div[class*="st-key-choice_"] button p,
    div[class*="st-key-allergy_"] button p,
    div[class*="st-key-category_"] button p,
    div[class*="st-key-item_"] button p {
        font-size: 22px;
        font-weight: 600;
    }
    div[class*="st-key-choice_"] button:hover,
    div[class*="st-key-allergy_"] button:hover,
    div[class*="st-key-category_"] button:hover,
    div[class*="st-key-item_"] button:hover {
        color: #2C6E78;
        border-bottom-color: #17233A;
        background: transparent;
    }
    div.st-key-back button {
        background: transparent;
        border: none;
        color: #17233A;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        font-size: 13px;
        padding-left: 0;
    }
    .sticker-wrap {
        display: flex;
        justify-content: center;
        padding: 8px 0 12px;
    }
    .sticker {
        width: 440px;
        min-height: 300px;
        box-sizing: border-box;
        background: #F6F2E9;
        border-radius: 18px;
        border: 1px solid rgba(23, 35, 58, 0.08);
        box-shadow: 0 10px 28px rgba(23, 35, 58, 0.08);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: 32px 36px 28px;
    }
    .sticker-kicker {
        margin-top: 16px;
        color: #8A8172;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 0.24em;
        text-transform: uppercase;
    }
    .sticker-name {
        margin-top: 10px;
        color: #17233A;
        font-weight: 700;
        letter-spacing: -0.035em;
        line-height: 1.08;
    }
    .name-short { font-size: 42px; }
    .name-medium { font-size: 34px; }
    .name-long { font-size: 30px; }
    .sticker-detail {
        display: block;
        margin-top: 8px;
        font-size: 22px;
        font-weight: 600;
        letter-spacing: -0.02em;
    }
    .sticker-rule {
        width: 56px;
        height: 2px;
        margin-top: 20px;
        background: #17233A;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div class="brand">
      {burst(TEAL, 72)}
      <div>
        <p class="brand-kicker">Catering</p>
        <h1>Étiquettes</h1>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)


def open_sticker(name: str, source: str):
    st.session_state.sticker_name = name
    st.session_state.sticker_from = source
    st.session_state.screen = "sticker"
    st.rerun()


if st.session_state.screen == "home":
    if st.button("Allergies", key="choice_allergies", use_container_width=True):
        st.session_state.screen = "allergies"
        st.rerun()
    if st.button("Articles", key="choice_articles", use_container_width=True):
        st.session_state.screen = "articles"
        st.rerun()
elif st.session_state.screen == "sticker":
    if st.button("Retour", key="back"):
        st.session_state.screen = st.session_state.sticker_from
        st.rerun()
    if st.session_state.sticker_from == "allergies":
        kicker = "Allergie"
        color = TEAL
    else:
        kicker = st.session_state.category or ""
        color = STAR_COLORS.get(kicker, NAVY)
    st.markdown(
        sticker_html(st.session_state.sticker_name, kicker, color),
        unsafe_allow_html=True,
    )
else:
    if st.button("Retour", key="back"):
        if st.session_state.screen == "items":
            st.session_state.screen = "articles"
            st.session_state.category = None
        else:
            st.session_state.screen = "home"
        st.rerun()

    if st.session_state.screen == "allergies":
        for index, label in enumerate(ALLERGIES):
            if st.button(label, key=f"allergy_{index}", use_container_width=True):
                open_sticker(label, "allergies")
    elif st.session_state.screen == "articles":
        for index, category in enumerate(ITEMS):
            if st.button(category, key=f"category_{index}", use_container_width=True):
                st.session_state.category = category
                st.session_state.screen = "items"
                st.rerun()
    elif st.session_state.category in ITEMS:
        for index, label in enumerate(ITEMS[st.session_state.category]):
            if st.button(label, key=f"item_{index}", use_container_width=True):
                open_sticker(label, "items")
