from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph

LABEL_NETWORK = "Nom du réseau | Network name"
LABEL_PASSWORD = "Mot de passe | Password"
FR_TITLE = "Instructions en français :"
EN_TITLE = "English Instructions:"
KEEP_LINE = "Gardez cette feuille comme référence | Keep this paper for future use"
TECH_TITLE = "Support technique | Technical support"
CLOSING_LINE = "Opticable | support@opticable.ca | 514-316-7236 #2"
QR_NOTE_FR = "À l'aide de votre appareil intelligent, vous pouvez scanner ce code QR pour accéder à votre réseau WiFi automatiquement sans y entrer de mot de passe."
QR_NOTE_EN = "With the help of your phone/tablet, you can scan this QR code to access your WiFi network automatically."

FR_ITEMS = [
    "Vous trouverez en haut de cette page le nom du réseau auquel vous connecter ainsi que le mot de passe à utiliser.",
    "Veuillez respecter les minuscules et majuscules dans le mot de passe",
    "L’utilisation d’internet est illimitée (téléchargement)",
    "Lorsque vous vous branchez au réseau internet de l’immeuble, vous reconnaissez avoir lu et accepté les termes et conditions sur cette page : opticable.ca/internet/termes",
    "Tous vos appareils sont compatibles avec le WiFi. Veuillez contacter notre équipe de support si l'un de vos périphériques n'arrive pas à se connecter.",
]

EN_ITEMS = [
    "At the top of this page, you will find the name of your network and the password required to connect.",
    "Please respect lower and upper cases in the password",
    "Internet usage is unlimited (Download)",
    "When you connect to the building’s internet network, you acknowledge that you have read and accepted the terms and conditions on this page : opticable.ca/internet/terms",
    "All your devices are compatible with WiFi. If some require a special configuration, please contact us if any of your devices cannot connect",
]

TECH_ITEMS = [
    "www.opticable.ca",
    "support@opticable.ca",
    "514-316-7236 #2",
]
def draw_card(
    canvas: Canvas,
    x: float,
    y: float,
    width: float,
    height: float,
    fill_color: colors.Color,
    radius: float,
    stroke_color: colors.Color | None = None,
) -> None:
    canvas.saveState()
    canvas.setFillColor(fill_color)
    canvas.setStrokeColor(stroke_color or fill_color)
    canvas.roundRect(x, y, width, height, radius, stroke=1 if stroke_color else 0, fill=1)
    canvas.restoreState()


def draw_paragraph(
    canvas: Canvas,
    text: str,
    x: float,
    y_top: float,
    width: float,
    font_name: str,
    font_size: float,
    color: colors.Color,
    leading: float | None = None,
    bold_fragments: bool = False,
) -> float:
    paragraph_text = text if bold_fragments else text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    style = ParagraphStyle(
        name=f"style-{font_name}-{font_size}",
        fontName=font_name,
        fontSize=font_size,
        leading=leading or font_size * 1.25,
        textColor=color,
        spaceAfter=0,
        spaceBefore=0,
    )
    paragraph = Paragraph(paragraph_text.replace("\n", "<br/>"), style)
    _, height = paragraph.wrap(width, 10_000)
    paragraph.drawOn(canvas, x, y_top - height)
    return height


def fit_font_size(value: str, font_name: str, max_width: float, start: int, minimum: int) -> int:
    font_size = start
    while font_size > minimum and pdfmetrics.stringWidth(value, font_name, font_size) > max_width:
        font_size -= 1
    return font_size


def draw_logo(canvas: Canvas, logo_path: Path | None, x: float, y: float, width: float, height: float) -> None:
    if not logo_path or not logo_path.exists():
        return
    canvas.drawImage(
        ImageReader(str(logo_path)),
        x,
        y,
        width=width,
        height=height,
        preserveAspectRatio=True,
        mask="auto",
    )


def draw_qr(canvas: Canvas, qr_path: Path, x: float, y: float, width: float, height: float) -> None:
    canvas.drawImage(
        ImageReader(str(qr_path)),
        x,
        y,
        width=width,
        height=height,
        preserveAspectRatio=True,
        mask="auto",
    )


def draw_bullet_list(
    canvas: Canvas,
    items: list[str],
    x: float,
    y_top: float,
    width: float,
    font_name: str,
    font_size: float,
    text_color: colors.Color,
    bullet_color: colors.Color,
    leading: float,
    gap: float = 3.0,
) -> float:
    current_top = y_top
    for item in items:
        canvas.saveState()
        canvas.setFillColor(bullet_color)
        canvas.circle(x + 3, current_top - 8, 1.8, stroke=0, fill=1)
        canvas.restoreState()
        height = draw_paragraph(
            canvas,
            item,
            x + 12,
            current_top,
            width - 12,
            font_name,
            font_size,
            text_color,
            leading=leading,
        )
        current_top -= height + gap
    return current_top


def draw_label_value_panel(
    canvas: Canvas,
    x: float,
    y: float,
    width: float,
    height: float,
    radius: float,
    label_width: float,
    fonts: dict[str, str],
    theme: dict[str, colors.Color],
    ssid: str,
    password: str,
    label_font_size: float = 10.5,
    ssid_start_size: int = 20,
    ssid_min_size: int = 12,
    password_start_size: int = 19,
    password_min_size: int = 11,
    center_values: bool = False,
) -> None:
    row_height = height / 2
    panel_path = canvas.beginPath()
    panel_path.roundRect(x, y, width, height, radius)

    canvas.saveState()
    canvas.setFillColor(theme["panel_background"])
    canvas.drawPath(panel_path, stroke=0, fill=1)
    canvas.clipPath(panel_path, stroke=0, fill=0)
    canvas.setFillColor(theme["label_band"])
    canvas.rect(x, y, label_width, height, fill=1, stroke=0)
    canvas.restoreState()

    canvas.saveState()
    canvas.setStrokeColor(theme["panel_border"])
    canvas.drawPath(panel_path, stroke=1, fill=0)
    canvas.line(x, y + row_height, x + width, y + row_height)
    canvas.line(x + label_width, y, x + label_width, y + height)
    canvas.restoreState()

    canvas.setFillColor(theme["label_text"])
    canvas.setFont(fonts["bold"], label_font_size)
    canvas.drawString(x + 12, y + row_height + 13, LABEL_NETWORK)
    canvas.drawString(x + 12, y + 13, LABEL_PASSWORD)

    ssid_font = fit_font_size(ssid, fonts["bold"], width - label_width - 24, ssid_start_size, ssid_min_size)
    pwd_font = fit_font_size(password, fonts["bold"], width - label_width - 24, password_start_size, password_min_size)
    value_area_x = x + label_width
    value_area_width = width - label_width
    canvas.setFillColor(theme["value_text"])
    canvas.setFont(fonts["bold"], ssid_font)
    ssid_x = x + label_width + 12
    ssid_y = y + row_height + 10
    pwd_x = x + label_width + 12
    pwd_y = y + 10
    if center_values:
        ssid_width = pdfmetrics.stringWidth(ssid, fonts["bold"], ssid_font)
        pwd_width = pdfmetrics.stringWidth(password, fonts["bold"], pwd_font)
        ssid_x = value_area_x + max((value_area_width - ssid_width) / 2, 12)
        pwd_x = value_area_x + max((value_area_width - pwd_width) / 2, 12)
        ssid_y = y + row_height + ((row_height - ssid_font) / 2) - 1
        pwd_y = y + ((row_height - pwd_font) / 2) - 1
    canvas.drawString(ssid_x, ssid_y, ssid)
    canvas.setFont(fonts["bold"], pwd_font)
    canvas.drawString(pwd_x, pwd_y, password)

