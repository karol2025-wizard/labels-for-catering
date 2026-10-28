import base64
import html
import os
from io import BytesIO

import streamlit as st
import streamlit.components.v1 as components
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

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

TEAL = "#6EAFC0"
LABEL_W = 3 * inch
LABEL_H = 1 * inch
FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")


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


def label_lines(name: str) -> list[str]:
    if " — " in name:
        return [part.strip() for part in name.split(" — ", 1)]
    return [name]


def _register_fonts() -> None:
    if "Outfit-Bold" in pdfmetrics.getRegisteredFontNames():
        return
    pdfmetrics.registerFont(TTFont("Outfit", os.path.join(FONT_DIR, "Outfit-Regular.ttf")))
    pdfmetrics.registerFont(TTFont("Outfit-Bold", os.path.join(FONT_DIR, "Outfit-Bold.ttf")))


def _fit_size(text: str, font: str, max_width: float, start: float, minimum: float) -> float:
    size = start
    while size > minimum and pdfmetrics.stringWidth(text, font, size) > max_width:
        size -= 0.25
    return size


def _draw_burst(pdf: canvas.Canvas, cx: float, cy: float, ink: tuple[float, float, float]) -> None:
    pdf.setFillColorRGB(*ink)
    for angle in (0, 45, 90, 135):
        pdf.saveState()
        pdf.translate(cx, cy)
        pdf.rotate(angle)
        pdf.ellipse(-5.2, -15.5, 5.2, 15.5, fill=1, stroke=0)
        pdf.restoreState()


def build_label_pdf(name: str, kicker: str, inverted: bool = False) -> bytes:
    _register_fonts()
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=(LABEL_W, LABEL_H))
    ink = (1, 1, 1) if inverted else (0, 0, 0)
    if inverted:
        pdf.setFillColorRGB(0, 0, 0)
        pdf.rect(0, 0, LABEL_W, LABEL_H, fill=1, stroke=0)
    _draw_burst(pdf, 26, LABEL_H / 2, ink)

    lines = label_lines(name)
    text_x = 48
    max_width = LABEL_W - text_x - 8
    kicker_size = 7 if inverted else 6.5
    kicker_font = "Outfit-Bold" if inverted else "Outfit"
    pdf.setFillColorRGB(*ink)
    if len(lines) == 1:
        name_size = _fit_size(lines[0], "Outfit-Bold", max_width, 16, 10)
        block = kicker_size + 4 + name_size
        top = (LABEL_H + block) / 2
        pdf.setFont(kicker_font, kicker_size)
        pdf.drawString(text_x, top - kicker_size, kicker.upper())
        pdf.setFont("Outfit-Bold", name_size)
        pdf.drawString(text_x, top - kicker_size - 4 - name_size, lines[0])
    else:
        first = _fit_size(lines[0], "Outfit-Bold", max_width, 13, 9)
        second = _fit_size(lines[1], "Outfit-Bold", max_width, 11, 8)
        block = kicker_size + 3 + first + 2 + second
        top = (LABEL_H + block) / 2
        pdf.setFont(kicker_font, kicker_size)
        pdf.drawString(text_x, top - kicker_size, kicker.upper())
        pdf.setFont("Outfit-Bold", first)
        pdf.drawString(text_x, top - kicker_size - 3 - first, lines[0])
        pdf.setFont("Outfit-Bold", second)
        pdf.drawString(text_x, top - kicker_size - 3 - first - 2 - second, lines[1])

    pdf.showPage()
    pdf.save()
    return buffer.getvalue()


def sticker_html(name: str, kicker: str, inverted: bool = False) -> str:
    lines = label_lines(name)
    if len(lines) == 1:
        if len(lines[0]) > 24:
            size = "label-name label-name-long"
        elif len(lines[0]) > 18:
            size = "label-name label-name-medium"
        else:
            size = "label-name"
        name_html = f'<div class="{size}">{html.escape(lines[0])}</div>'
    else:
        name_html = (
            f'<div class="label-name label-name-two">{html.escape(lines[0])}</div>'
            f'<div class="label-name label-name-sub">{html.escape(lines[1])}</div>'
        )
    return f"""
    <div class="label-slot">
      <div class="label-zoom">
        <div class="label{' label-allergy' if inverted else ''}">
          {burst("#ffffff" if inverted else "#111111", "0.58in")}
          <div class="label-copy">
            <div class="label-kicker">{html.escape(kicker)}</div>
            {name_html}
          </div>
        </div>
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
    .label-slot {
        height: 2.5in;
        display: flex;
        justify-content: center;
        align-items: flex-start;
        margin-top: 10px;
    }
    .label-zoom {
        width: 3in;
        height: 1in;
        transform: scale(2.5);
        transform-origin: top center;
    }
    .label {
        width: 3in;
        height: 1in;
        box-sizing: border-box;
        background: #ffffff;
        color: #111111;
        display: flex;
        align-items: center;
        gap: 0.1in;
        padding: 0.08in 0.12in 0.08in 0.1in;
        border: 1px solid #111111;
    }
    .label-allergy {
        background: #111111;
        color: #ffffff;
    }
    .label-copy {
        min-width: 0;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .label-allergy .label-kicker {
        font-weight: 700;
    }
    .label-kicker {
        margin: 0 0 1px;
        font-size: 7pt;
        font-weight: 700;
        letter-spacing: 0.16em;
        text-transform: uppercase;
        line-height: 1;
    }
    .label-name {
        font-size: 16pt;
        font-weight: 700;
        letter-spacing: -0.03em;
        line-height: 1.02;
        white-space: nowrap;
    }
    .label-name-medium { font-size: 13.5pt; }
    .label-name-long { font-size: 12pt; }
    .label-name-two { font-size: 13pt; white-space: nowrap; }
    .label-name-sub { font-size: 11pt; margin-top: 1px; white-space: nowrap; }
    .label-meta {
        text-align: center;
        color: #5c564c;
        font-size: 13px;
        letter-spacing: 0.04em;
        margin: 8px 0 4px;
    }
    @media print {
        @page { size: 3in 1in; margin: 0; }
        .brand, .label-meta, [data-testid="stHeader"], [data-testid="stToolbar"],
        footer, [data-testid="stDownloadButton"], .stButton {
            display: none !important;
        }
        .label-slot { height: 1in; margin: 0; }
        .label-zoom { transform: none; }
        .label { border: none; }
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
    inverted = st.session_state.sticker_from == "allergies"
    kicker = "Allergie" if inverted else (st.session_state.category or "")
    st.markdown(
        sticker_html(st.session_state.sticker_name, kicker, inverted),
        unsafe_allow_html=True,
    )
    pdf_b64 = base64.b64encode(
        build_label_pdf(st.session_state.sticker_name, kicker, inverted)
    ).decode("ascii")
    components.html(
        f"""
        <button id="print" type="button">Imprimer</button>
        <script>
          const pdfB64 = "{pdf_b64}";
          document.getElementById("print").onclick = () => {{
            const raw = atob(pdfB64);
            const bytes = new Uint8Array(raw.length);
            for (let i = 0; i < raw.length; i++) bytes[i] = raw.charCodeAt(i);
            const url = URL.createObjectURL(new Blob([bytes], {{type: "application/pdf"}}));
            const frame = document.createElement("iframe");
            frame.setAttribute("aria-hidden", "true");
            frame.style.position = "fixed";
            frame.style.width = "0";
            frame.style.height = "0";
            frame.style.border = "0";
            document.body.appendChild(frame);
            frame.onload = () => {{
              setTimeout(() => {{
                frame.contentWindow.focus();
                frame.contentWindow.print();
              }}, 300);
            }};
            frame.src = url;
          }};
        </script>
        <style>
          html, body {{
            margin: 0;
            background: #E4DFD3;
            font-family: Outfit, "Segoe UI", sans-serif;
          }}
          #print {{
            width: 100%;
            height: 44px;
            border: 1px solid rgba(23, 35, 58, 0.2);
            border-radius: 8px;
            background: #F6F2E9;
            color: #17233A;
            font: 600 16px Outfit, "Segoe UI", sans-serif;
            cursor: pointer;
          }}
          #print:hover {{ border-color: #17233A; }}
        </style>
        """,
        height=52,
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
