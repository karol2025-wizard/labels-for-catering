import base64
import html
import os
import re
import zlib
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
        "For Fattouch",
        "For Zesty",
        "Fried Pita",
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
    "Kit": [
        "Crispy Taouk Kit",
        "Saumon Kit",
        "Shawarma Agneau Kit",
        "Shish Taouk Kit",
        "Riz",
        "Quinoa",
    ],
    "Plats Individus": [
        "Lamb Shawarma Plate",
        "Shish Taouk Plate",
        "Mix Plate — Shish Taouk + Lamb",
        "Salmon Plate",
        "Hummus Shawarma — Lamb",
        "Falafel",
        "Cauliflower",
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
        "Cookies Kit",
    ],
}

NOTES = {"For Fattouch", "For Zesty", "Fried Pita"}

SKIP_ORDER_ITEMS = ("yalanji", "chou-fleur", "chou fleur", "trempette")


def _pdf_lines(data: bytes) -> list[str]:
    lines = []
    for stream in re.findall(rb"stream\r?\n(.*?)\r?\nendstream", data, re.S):
        try:
            text = zlib.decompress(stream).decode("latin1")
        except zlib.error:
            continue
        for block in re.findall(r"\[(.*?)\] TJ", text, re.S):
            parts = re.findall(r"<([0-9A-Fa-f]+)>", block)
            if not parts:
                continue
            line = bytes.fromhex("".join(parts)).decode("latin1").strip()
            if line:
                lines.append(line)
    return lines


def _skip_order_item(name: str) -> bool:
    folded = name.lower()
    return any(token in folded for token in SKIP_ORDER_ITEMS)


def _sticker_for_item(name: str) -> str | None:
    if _skip_order_item(name):
        return None
    folded = name.lower()
    folded = re.sub(r"\s*\(traiteur\)", "", folded)
    folded = re.sub(r"\s*-\s*traiteur\s*$", "", folded)
    folded = re.sub(r"\s*-\s*\d+\s*pcs", "", folded)
    folded = re.sub(r"\s+", " ", folded).strip(" -")
    if "fattouch" in folded and "zesty" in folded:
        return "Zesty Fattouch"
    if "fattouch" in folded:
        return "Classic Fattouch"
    if "kibbeh" in folded:
        return "Kibbeh Pistaches"
    if "shish taouk" in folded and "kit" in folded:
        return "Shish Taouk Kit"
    if "shawarma" in folded and "agneau" in folded and "kit" in folded:
        return "Shawarma Agneau Kit"
    if "crispy taouk" in folded and "kit" in folded:
        return "Crispy Taouk Kit"
    if "saumon" in folded and "kit" in folded:
        return "Saumon Kit"
    if folded == "riz":
        return "Riz"
    if "quinoa" in folded:
        return "Quinoa"
    return None


def _sticker_for_component(parent: str | None, name: str) -> str | None:
    if not parent:
        return None
    folded = name.lower()
    if "fried pita" in folded:
        return "Fried Pita"
    if "dressing" in folded:
        if parent == "Zesty Fattouch":
            return "For Zesty"
        if parent == "Classic Fattouch":
            return "For Fattouch"
    return None


def order_stickers(data: bytes) -> tuple[str, list[tuple[str, int]], list[str]]:
    lines = _pdf_lines(data)
    order_id = next((line for line in lines if line.startswith("FOL-") and "MANAGER" not in line), "")
    try:
        index = lines.index("ARTICLES") + 1
    except ValueError:
        return order_id, [], []
    queue: list[tuple[str, int]] = []
    left_out: list[str] = []
    while index < len(lines):
        line = lines[index]
        if "MANAGER" in line or line.startswith("Sous-total"):
            break
        qty_match = re.fullmatch(r"(\d+)x", line)
        if not qty_match:
            index += 1
            continue
        quantity = int(qty_match.group(1))
        index += 1
        if index >= len(lines):
            break
        raw_name = lines[index]
        index += 1
        sticker = _sticker_for_item(raw_name)
        if sticker:
            queue.append((sticker, quantity))
        else:
            left_out.append(raw_name)
        while index < len(lines) and not re.fullmatch(r"\d+x", lines[index]) and "MANAGER" not in lines[index]:
            if re.fullmatch(r"\d+", lines[index]):
                component_qty = int(lines[index])
                index += 1
                if index >= len(lines):
                    break
                component = lines[index]
                index += 1
                child = _sticker_for_component(sticker, component)
                if child:
                    queue.append((child, component_qty))
                elif sticker:
                    left_out.append(component)
            else:
                index += 1
    return order_id, queue, left_out


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
    pdf.setFillColorRGB(*ink)
    if kicker and len(lines) == 1:
        kicker_size = 7
        name_size = _fit_size(lines[0], "Outfit-Bold", max_width, 16, 10)
        block = kicker_size + 4 + name_size
        top = (LABEL_H + block) / 2
        pdf.setFont("Outfit-Bold", kicker_size)
        pdf.drawString(text_x, top - kicker_size, kicker.upper())
        pdf.setFont("Outfit-Bold", name_size)
        pdf.drawString(text_x, top - kicker_size - 4 - name_size, lines[0])
    elif kicker:
        kicker_size = 7
        first = _fit_size(lines[0], "Outfit-Bold", max_width, 13, 9)
        second = _fit_size(lines[1], "Outfit-Bold", max_width, 11, 8)
        block = kicker_size + 3 + first + 2 + second
        top = (LABEL_H + block) / 2
        pdf.setFont("Outfit-Bold", kicker_size)
        pdf.drawString(text_x, top - kicker_size, kicker.upper())
        pdf.setFont("Outfit-Bold", first)
        pdf.drawString(text_x, top - kicker_size - 3 - first, lines[0])
        pdf.setFont("Outfit-Bold", second)
        pdf.drawString(text_x, top - kicker_size - 3 - first - 2 - second, lines[1])
    elif len(lines) == 1:
        name_size = _fit_size(lines[0], "Outfit-Bold", max_width, 22, 12)
        pdf.setFont("Outfit-Bold", name_size)
        pdf.drawString(text_x, (LABEL_H - name_size) / 2 + 1, lines[0])
    else:
        first = _fit_size(lines[0], "Outfit-Bold", max_width, 16, 11)
        second = _fit_size(lines[1], "Outfit-Bold", max_width, 13, 9)
        block = first + 3 + second
        top = (LABEL_H + block) / 2
        pdf.setFont("Outfit-Bold", first)
        pdf.drawString(text_x, top - first, lines[0])
        pdf.setFont("Outfit-Bold", second)
        pdf.drawString(text_x, top - first - 3 - second, lines[1])

    pdf.showPage()
    pdf.save()
    return buffer.getvalue()


def label_markup(name: str, kicker: str, inverted: bool) -> str:
    lines = label_lines(name)
    if len(lines) == 1:
        if len(lines[0]) > 24:
            size = "label-name label-name-long"
        elif len(lines[0]) > 18:
            size = "label-name label-name-medium"
        else:
            size = "label-name"
        if not kicker:
            size += " label-solo"
        if name in NOTES:
            size += " label-script"
        name_html = f'<div class="{size}">{html.escape(lines[0])}</div>'
    else:
        name_html = (
            f'<div class="label-name label-name-two">{html.escape(lines[0])}</div>'
            f'<div class="label-name label-name-sub">{html.escape(lines[1])}</div>'
        )
    kicker_html = (
        f'<div class="label-kicker">{html.escape(kicker)}</div>' if kicker else ""
    )
    allergy = " label-allergy" if inverted else ""
    star = burst("#ffffff" if inverted else "#111111", "0.58in")
    return (
        f'<div class="label{allergy}">{star}'
        f'<div class="label-copy">{kicker_html}{name_html}</div></div>'
    )


def sticker_html(name: str, kicker: str, inverted: bool = False) -> str:
    return (
        '<div class="label-slot"><div class="label-zoom">'
        f"{label_markup(name, kicker, inverted)}"
        "</div></div>"
    )


def print_page(name: str, kicker: str, inverted: bool) -> str:
    font = base64.b64encode(
        open(os.path.join(FONT_DIR, "Outfit-Bold.ttf"), "rb").read()
    ).decode("ascii")
    bg = "#111111" if inverted else "#ffffff"
    ink = "#ffffff" if inverted else "#111111"
    plate = (
        '<svg class="ink-plate" xmlns="http://www.w3.org/2000/svg" '
        'width="3in" height="1in" viewBox="0 0 300 100" preserveAspectRatio="none">'
        '<rect width="300" height="100" fill="#000000"/></svg>'
        if inverted
        else ""
    )
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Etiquette</title>
<style>
@font-face {{
  font-family: Outfit;
  font-weight: 700;
  src: url(data:font/ttf;base64,{font}) format("truetype");
}}
@page {{ size: 3in 1in; margin: 0; }}
html, body {{
  margin: 0;
  width: 3in;
  height: 1in;
  overflow: hidden;
  background: {bg};
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}}
body {{ position: relative; }}
.ink-plate {{
  position: absolute;
  left: 0;
  top: 0;
  width: 3in;
  height: 1in;
  z-index: 0;
}}
.label {{
  position: relative;
  z-index: 1;
  width: 3in;
  height: 1in;
  box-sizing: border-box;
  background: {bg};
  color: {ink};
  display: flex;
  align-items: center;
  gap: 0.1in;
  padding: 0.08in 0.12in 0.08in 0.1in;
  font-family: Outfit, Arial, sans-serif;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}}
.label-copy {{ display: flex; flex-direction: column; justify-content: center; }}
.label-kicker {{
  font-size: 7pt; font-weight: 700; letter-spacing: 0.16em;
  text-transform: uppercase; line-height: 1; margin: 0 0 1px;
}}
.label-name {{ font-size: 16pt; font-weight: 700; letter-spacing: -0.03em; line-height: 1.02; white-space: nowrap; }}
.label-name-medium {{ font-size: 13.5pt; }}
.label-name-long {{ font-size: 12pt; }}
.label-solo {{ font-size: 20pt; }}
.label-name-two {{ font-size: 13pt; }}
.label-name-sub {{ font-size: 11pt; margin-top: 1px; }}
.label-name.label-script {{
  font-family: Georgia, "Palatino Linotype", Palatino, serif;
  font-style: italic;
  font-weight: 500;
  letter-spacing: 0.01em;
}}
</style>
</head>
<body>
{plate}
{label_markup(name, kicker, inverted)}
</body>
</html>"""


def print_batch(names: list[str]) -> str:
    font = base64.b64encode(
        open(os.path.join(FONT_DIR, "Outfit-Bold.ttf"), "rb").read()
    ).decode("ascii")
    labels = "".join(label_markup(name, "", False) for name in names)
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Etiquettes</title>
<style>
@font-face {{
  font-family: Outfit;
  font-weight: 700;
  src: url(data:font/ttf;base64,{font}) format("truetype");
}}
@page {{ size: 3in 1in; margin: 0; }}
html, body {{
  margin: 0;
  background: #ffffff;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}}
.label {{
  position: relative;
  width: 3in;
  height: 1in;
  box-sizing: border-box;
  background: #ffffff;
  color: #111111;
  display: flex;
  align-items: center;
  gap: 0.1in;
  padding: 0.08in 0.12in 0.08in 0.1in;
  font-family: Outfit, Arial, sans-serif;
  overflow: hidden;
  break-after: page;
  page-break-after: always;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}}
.label:last-child {{ break-after: auto; page-break-after: auto; }}
.label-copy {{ display: flex; flex-direction: column; justify-content: center; }}
.label-name {{ font-size: 16pt; font-weight: 700; letter-spacing: -0.03em; line-height: 1.02; white-space: nowrap; }}
.label-name-medium {{ font-size: 13.5pt; }}
.label-name-long {{ font-size: 12pt; }}
.label-solo {{ font-size: 20pt; }}
.label-name-two {{ font-size: 13pt; }}
.label-name-sub {{ font-size: 11pt; margin-top: 1px; }}
.label-name.label-script {{
  font-family: Georgia, "Palatino Linotype", Palatino, serif;
  font-style: italic;
  font-weight: 500;
  letter-spacing: 0.01em;
}}
</style>
</head>
<body>
{labels}
</body>
</html>"""


def imprimer_button(page: str) -> None:
    encoded = base64.b64encode(page.encode("utf-8")).decode("ascii")
    components.html(
        f"""
        <button id="print" type="button">Imprimer</button>
        <script>
          const page = atob("{encoded}");
          const parentDoc = window.parent.document;
          let frame = parentDoc.getElementById("label-print-frame");
          if (frame) frame.remove();
          frame = parentDoc.createElement("iframe");
          frame.id = "label-print-frame";
          frame.setAttribute("style", "position:fixed;width:3in;height:1in;border:0;left:0;top:0;transform:translate(-120vw,0);pointer-events:none;");
          let ready = false;
          frame.onload = () => {{
            const fonts = frame.contentWindow.document.fonts;
            const mark = () => {{ ready = true; }};
            if (fonts && fonts.ready) fonts.ready.then(mark);
            else mark();
          }};
          parentDoc.body.appendChild(frame);
          frame.srcdoc = page;
          document.getElementById("print").onclick = () => {{
            const go = () => {{
              frame.contentWindow.focus();
              frame.contentWindow.print();
            }};
            if (ready) go();
            else {{
              const fonts = frame.contentWindow.document.fonts;
              (fonts && fonts.ready ? fonts.ready : Promise.resolve()).then(go);
            }}
          }};
        </script>
        <style>
          html, body {{ margin: 0; background: #E4DFD3; }}
          #print {{
            width: 100%;
            height: 44px;
            border: 1px solid rgba(23, 35, 58, 0.2);
            border-radius: 8px;
            background: #F6F2E9;
            color: #17233A;
            font: 600 16px "Segoe UI", sans-serif;
            cursor: pointer;
          }}
        </style>
        """,
        height=52,
    )


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
    div[class*="st-key-item_"] button,
    div[class*="st-key-note_"] button {
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
    div[class*="st-key-note_"] button,
    div[class*="st-key-note_"] button p {
        font-family: Georgia, "Palatino Linotype", Palatino, serif;
        font-style: italic;
        font-weight: 500;
        font-size: 20px;
        letter-spacing: 0.01em;
    }
    div[class*="st-key-choice_"] button:hover,
    div[class*="st-key-allergy_"] button:hover,
    div[class*="st-key-category_"] button:hover,
    div[class*="st-key-item_"] button:hover,
    div[class*="st-key-note_"] button:hover {
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
    .label-solo { font-size: 20pt; }
    .label-name-long { font-size: 12pt; }
    .label-name-two { font-size: 13pt; white-space: nowrap; }
    .label-name-sub { font-size: 11pt; margin-top: 1px; white-space: nowrap; }
    .queue-row {
        display: flex;
        gap: 16px;
        align-items: baseline;
        min-height: 52px;
        border-bottom: 1px solid rgba(23, 35, 58, 0.18);
        color: #17233A;
        font-size: 22px;
        font-weight: 600;
        padding: 12px 4px;
    }
    .queue-row span { min-width: 28px; }
    .queue-note {
        font-family: Georgia, "Palatino Linotype", Palatino, serif;
        font-style: italic;
        font-weight: 500;
        font-size: 20px;
    }
    .queue-aside {
        margin: 18px 4px 0;
        color: #17233A;
        font-size: 14px;
        line-height: 1.4;
    }
    .label-name.label-script {
        font-family: Georgia, "Palatino Linotype", Palatino, serif;
        font-style: italic;
        font-weight: 500;
        letter-spacing: 0.01em;
    }
    a.print-link {
        display: block;
        width: min(100%, 7.5in);
        margin: 14px auto 0;
        height: 44px;
        line-height: 44px;
        box-sizing: border-box;
        border: 1px solid rgba(23, 35, 58, 0.2);
        border-radius: 8px;
        background: #F6F2E9;
        color: #17233A;
        font-size: 16px;
        font-weight: 600;
        text-align: center;
        text-decoration: none;
    }
    a.print-link:hover { border-color: #17233A; color: #17233A; }
    @media print {
        @page { size: 3in 1in; margin: 0; }
        html, body, .stApp, [data-testid="stAppViewContainer"],
        [data-testid="stMain"], section.main, .block-container {
            background: #fff !important;
            margin: 0 !important;
            padding: 0 !important;
            height: 1in !important;
            min-height: 0 !important;
            overflow: hidden !important;
        }
        .brand, header, footer, [data-testid="stHeader"],
        [data-testid="stToolbar"], [data-testid="stDecoration"],
        .stButton, iframe {
            display: none !important;
        }
        .label-slot {
            height: 1in !important;
            margin: 0 !important;
            display: block !important;
        }
        .label-zoom { transform: none !important; }
        .label { border: none !important; }
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
    if st.button("Commande", key="choice_order", use_container_width=True):
        st.session_state.screen = "order"
        st.rerun()
elif st.session_state.screen == "sticker":
    if st.button("Retour", key="back"):
        st.session_state.screen = st.session_state.sticker_from
        st.rerun()
    inverted = st.session_state.sticker_from == "allergies"
    kicker = "Allergie" if inverted else ""
    st.markdown(
        sticker_html(st.session_state.sticker_name, kicker, inverted),
        unsafe_allow_html=True,
    )
    imprimer_button(print_page(st.session_state.sticker_name, kicker, inverted))
elif st.session_state.screen == "order":
    if st.button("Retour", key="back"):
        st.session_state.screen = "home"
        st.rerun()
    uploaded = st.file_uploader("PDF de la commande", type=["pdf"])
    if uploaded is not None:
        order_id, queue, left_out = order_stickers(uploaded.getvalue())
        if order_id:
            st.markdown(f'<p class="brand-kicker">{html.escape(order_id)}</p>', unsafe_allow_html=True)
        if queue:
            rows = []
            for name, count in queue:
                note = " queue-note" if name in NOTES else ""
                rows.append(
                    f'<div class="queue-row{note}"><span>{count}</span>{html.escape(name)}</div>'
                )
            st.markdown("".join(rows), unsafe_allow_html=True)
            copies = [name for name, count in queue for _ in range(count)]
            imprimer_button(print_batch(copies))
        else:
            st.markdown('<p class="queue-aside">Aucune étiquette dans ce PDF.</p>', unsafe_allow_html=True)
        if left_out:
            names = ", ".join(html.escape(name) for name in left_out)
            st.markdown(f'<p class="queue-aside">Non imprimé : {names}</p>', unsafe_allow_html=True)
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
            key = f"note_{index}" if label in NOTES else f"item_{index}"
            if st.button(label, key=key, use_container_width=True):
                open_sticker(label, "items")
