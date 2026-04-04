from __future__ import annotations

from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph

from ..models import WifiRecord


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


def draw_numbered_list(
    canvas: Canvas,
    items: list[str],
    x: float,
    y_top: float,
    width: float,
    font_name: str,
    font_size: float,
    text_color: colors.Color,
    number_color: colors.Color,
    leading: float,
    gap: float = 3.0,
) -> float:
    current_top = y_top
    for index, item in enumerate(items, start=1):
        canvas.setFillColor(number_color)
        canvas.setFont(font_name, font_size)
        canvas.drawString(x, current_top - 9, f"{index}.")
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


def draw_sheet_layout(
    canvas: Canvas,
    record: WifiRecord,
    building_name: str,
    qr_path: Path,
    settings: Any,
    fonts: dict[str, str],
    theme: dict[str, colors.Color | str],
) -> None:
    page_width, page_height = canvas._pagesize
    margin = 26
    radius = 14
    header_height = 88
    header_bottom = page_height - header_height

    panel_width = page_width - (2 * margin)
    label_width = 195
    instructions_gap = 16
    column_width = (panel_width - instructions_gap) / 2

    canvas.setTitle(f"{building_name} - {record.ssid}")
    canvas.setAuthor(settings.branding.brand_name)
    canvas.setFillColor(theme["page_background"])
    canvas.rect(0, 0, page_width, page_height, fill=1, stroke=0)

    if theme["variant"] == "basic":
        _draw_basic_layout(canvas, record, building_name, qr_path, settings, fonts, theme)
        return

    if theme["variant"] == "legacy":
        canvas.setFillColor(theme["header_accent"])
        canvas.rect(0, page_height - 12, page_width, 12, fill=1, stroke=0)
        canvas.setFillColor(theme["header_background"])
        canvas.rect(0, header_bottom, page_width, header_height - 12, fill=1, stroke=0)
        draw_logo(canvas, settings.branding.logo_path, margin, header_bottom + 24, 170, 34)
        canvas.setStrokeColor(theme["header_accent"])
        canvas.setLineWidth(2)
        canvas.line(margin, header_bottom + 16, page_width - margin - 92, header_bottom + 16)
        draw_card(canvas, page_width - margin - 80, header_bottom + 10, 80, 68, colors.white, 10, theme["qr_border"])
        draw_qr(canvas, qr_path, page_width - margin - 72, header_bottom + 16, 56, 56)
    elif theme["variant"] == "modern":
        canvas.setFillColor(theme["header_background"])
        canvas.rect(0, header_bottom, page_width, header_height, fill=1, stroke=0)
        canvas.setFillColor(theme["header_accent"])
        canvas.circle(page_width - 36, page_height - 26, 44, fill=1, stroke=0)
        canvas.setFillColor(theme["header_secondary"])
        canvas.circle(page_width - 94, header_bottom + 24, 30, fill=1, stroke=0)
        draw_card(canvas, margin, header_bottom + 14, 196, 56, colors.white, 18)
        draw_logo(canvas, settings.branding.logo_path, margin + 14, header_bottom + 25, 168, 28)
        draw_card(canvas, page_width - margin - 88, header_bottom + 10, 88, 68, colors.white, 16)
        draw_qr(canvas, qr_path, page_width - margin - 78, header_bottom + 16, 60, 56)
        canvas.setStrokeColor(theme["header_rule"])
        canvas.setLineWidth(1.2)
        canvas.line(margin + 208, header_bottom + 42, page_width - margin - 98, header_bottom + 42)
    else:
        canvas.setFillColor(theme["header_background"])
        canvas.rect(0, header_bottom, page_width, header_height, fill=1, stroke=0)
        canvas.setStrokeColor(theme["header_rule"])
        canvas.setLineWidth(1.3)
        canvas.line(margin, header_bottom + 16, page_width - margin, header_bottom + 16)
        draw_logo(canvas, settings.branding.logo_path, margin, header_bottom + 31, 150, 30)
        draw_card(
            canvas,
            page_width - margin - 72,
            header_bottom + 10,
            72,
            64,
            colors.white,
            10,
            theme["qr_border"],
        )
        draw_qr(canvas, qr_path, page_width - margin - 63, header_bottom + 18, 54, 48)

    info_y = header_bottom - 92
    draw_label_value_panel(
        canvas,
        margin,
        info_y,
        panel_width,
        80,
        radius,
        label_width,
        fonts,
        theme,
        record.ssid,
        record.password or "",
    )

    instructions_y = info_y - 246
    for column_index, (title, items) in enumerate(((FR_TITLE, FR_ITEMS), (EN_TITLE, EN_ITEMS))):
        box_x = margin + (column_index * (column_width + instructions_gap))
        draw_card(canvas, box_x, instructions_y, column_width, 228, theme["section_background"], radius, theme["section_border"])
        if theme["variant"] == "basic":
            canvas.setStrokeColor(theme["section_border"])
            canvas.setLineWidth(0.9)
            canvas.line(box_x + 12, instructions_y + 194, box_x + column_width - 12, instructions_y + 194)
            canvas.setFillColor(theme["section_title_text"])
            canvas.setFont(fonts["bold"], 10)
            canvas.drawString(box_x + 14, instructions_y + 200, title)
        else:
            canvas.setFillColor(theme["section_title_band"])
            canvas.roundRect(box_x + 12, instructions_y + 192, column_width - 24, 24, 12, fill=1, stroke=0)
            canvas.setFillColor(theme["section_title_text"])
            canvas.setFont(fonts["bold"], 10)
            canvas.drawString(box_x + 20, instructions_y + 200, title)
        draw_bullet_list(
            canvas,
            items,
            box_x + 16,
            instructions_y + 184,
            column_width - 32,
            fonts["regular"],
            8.15,
            theme["body_text"],
            theme["bullet"],
            leading=9.3,
            gap=2.4,
        )

    note_y = instructions_y - 34
    draw_card(canvas, margin, note_y, panel_width, 24, theme["note_background"], 12)
    canvas.setFillColor(theme["note_text"])
    canvas.setFont(fonts["bold"], 9.2)
    canvas.drawCentredString(margin + (panel_width / 2), note_y + 8, KEEP_LINE)

    support_y = note_y - 138

    draw_card(canvas, margin, support_y, panel_width, 124, theme["support_background"], radius, theme["support_border"])

    canvas.setFillColor(theme["title_text"])
    canvas.setFont(fonts["bold"], 9.1)
    draw_paragraph(
        canvas,
        TECH_TITLE,
        margin + 14,
        support_y + 110,
        panel_width - 28,
        fonts["bold"],
        9.1,
        theme["title_text"],
        leading=10.2,
    )
    draw_bullet_list(
        canvas,
        TECH_ITEMS,
        margin + 14,
        support_y + 78,
        panel_width - 28,
        fonts["regular"],
        8.9,
        theme["body_text"],
        theme["bullet"],
        leading=10.0,
        gap=3.0,
    )

    closing_y = support_y - 40
    draw_card(canvas, margin, closing_y, panel_width, 30, theme["footer_background"], 14)
    canvas.setFillColor(theme["footer_text"])
    canvas.setFont(fonts["bold"], 8.8)
    draw_paragraph(
        canvas,
        CLOSING_LINE,
        margin + 14,
        closing_y + 20,
        panel_width - 28,
        fonts["bold"],
        8.8,
        theme["footer_text"],
        leading=9.6,
    )


def _draw_basic_layout(
    canvas: Canvas,
    record: WifiRecord,
    building_name: str,
    qr_path: Path,
    settings: Any,
    fonts: dict[str, str],
    theme: dict[str, colors.Color | str],
) -> None:
    page_width, page_height = canvas._pagesize
    margin = 22
    radius = 11
    header_height = 80
    header_bottom = page_height - header_height
    panel_width = page_width - (2 * margin)
    label_width = 186

    canvas.setFillColor(theme["header_background"])
    canvas.rect(0, header_bottom, page_width, header_height, fill=1, stroke=0)
    draw_logo(canvas, settings.branding.logo_path, margin, header_bottom + 31, 144, 26)
    canvas.setFillColor(theme["title_text"])
    canvas.setFont(fonts["bold"], 10.8)
    canvas.drawCentredString(page_width / 2, header_bottom + 58, building_name)
    canvas.setStrokeColor(theme["header_rule"])
    canvas.setLineWidth(1.3)
    canvas.line(margin, header_bottom + 18, page_width - margin, header_bottom + 18)
    draw_card(
        canvas,
        page_width - margin - 96,
        header_bottom - 2,
        96,
        78,
        colors.white,
        10,
        theme["qr_border"],
    )
    draw_qr(canvas, qr_path, page_width - margin - 84, header_bottom + 1, 72, 72)

    info_y = header_bottom - 74
    draw_label_value_panel(
        canvas,
        margin,
        info_y,
        panel_width,
        54,
        radius,
        label_width,
        fonts,
        theme,
        record.ssid,
        record.password or "",
        label_font_size=8.8,
        ssid_start_size=13,
        ssid_min_size=10,
        password_start_size=12,
        password_min_size=9,
    )

    qr_note_y = info_y - 76
    draw_card(canvas, margin, qr_note_y, panel_width, 64, theme["note_background"], 10, theme["panel_border"])
    canvas.setFillColor(theme["note_text"])
    canvas.setFont(fonts["bold"], 9.2)
    canvas.drawString(margin + 12, qr_note_y + 50, "Code QR | QR code")
    draw_paragraph(
        canvas,
        f"{QR_NOTE_FR}<br/>{QR_NOTE_EN}",
        margin + 12,
        qr_note_y + 38,
        panel_width - 24,
        fonts["regular"],
        9.0,
        theme["body_text"],
        leading=9.1,
        bold_fragments=True,
    )

    fr_y = 402
    fr_height = 148
    en_y = 262
    en_height = 126

    draw_card(canvas, margin, fr_y, panel_width, fr_height, theme["section_background"], radius, theme["section_border"])
    draw_card(canvas, margin, en_y, panel_width, en_height, theme["section_background"], radius, theme["section_border"])

    canvas.setFillColor(theme["section_title_text"])
    canvas.setFont(fonts["bold"], 10.8)
    canvas.drawString(margin + 14, fr_y + fr_height - 18, FR_TITLE)
    canvas.drawString(margin + 14, en_y + en_height - 18, EN_TITLE)
    canvas.setStrokeColor(theme["section_border"])
    canvas.setLineWidth(0.9)
    canvas.line(margin + 14, fr_y + fr_height - 24, margin + panel_width - 14, fr_y + fr_height - 24)
    canvas.line(margin + 14, en_y + en_height - 24, margin + panel_width - 14, en_y + en_height - 24)

    draw_bullet_list(
        canvas,
        FR_ITEMS,
        margin + 14,
        fr_y + fr_height - 30,
        panel_width - 28,
        fonts["regular"],
        9.35,
        theme["body_text"],
        theme["bullet"],
        leading=10.1,
        gap=1.5,
    )
    draw_bullet_list(
        canvas,
        EN_ITEMS,
        margin + 14,
        en_y + en_height - 30,
        panel_width - 28,
        fonts["regular"],
        9.45,
        theme["body_text"],
        theme["bullet"],
        leading=10.2,
        gap=1.7,
    )

    note_y = 238
    draw_card(canvas, margin, note_y, panel_width, 22, theme["note_background"], 11)
    canvas.setFillColor(theme["note_text"])
    canvas.setFont(fonts["bold"], 9.55)
    canvas.drawCentredString(margin + (panel_width / 2), note_y + 7, KEEP_LINE)

    support_y = 114
    support_height = 110

    draw_card(canvas, margin, support_y, panel_width, support_height, theme["support_background"], radius, theme["support_border"])

    draw_paragraph(
        canvas,
        TECH_TITLE,
        margin + 12,
        support_y + support_height - 12,
        panel_width - 24,
        fonts["bold"],
        9.85,
        theme["title_text"],
        leading=10.0,
    )
    draw_bullet_list(
        canvas,
        TECH_ITEMS,
        margin + 12,
        support_y + support_height - 41,
        panel_width - 24,
        fonts["regular"],
        9.6,
        theme["body_text"],
        theme["bullet"],
        leading=10.0,
        gap=2.5,
    )

    closing_y = 48
    draw_card(canvas, margin, closing_y, panel_width, 24, theme["footer_background"], 11)
    draw_paragraph(
        canvas,
        CLOSING_LINE,
        margin + 12,
        closing_y + 16,
        panel_width - 24,
        fonts["bold"],
        9.15,
        theme["footer_text"],
        leading=9.3,
    )

