from __future__ import annotations

from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.pdfgen.canvas import Canvas

from ..models import WifiRecord
from .common import (
    EN_ITEMS,
    EN_TITLE,
    FR_ITEMS,
    FR_TITLE,
    KEEP_LINE,
    draw_bullet_list,
    draw_card,
    draw_label_value_panel,
    draw_logo,
    draw_paragraph,
    draw_qr,
)


OPTICABLE_TEMPLATE_01_THEME = {
    "page_background": colors.HexColor("#F7FBF8"),
    "header_background": colors.white,
    "header_rule": colors.HexColor("#56B980"),
    "panel_background": colors.white,
    "panel_border": colors.HexColor("#D6E8DD"),
    "label_band": colors.HexColor("#2E8A67"),
    "label_text": colors.white,
    "value_text": colors.HexColor("#222328"),
    "section_background": colors.white,
    "section_border": colors.HexColor("#D6E8DD"),
    "section_title_text": colors.HexColor("#274035"),
    "body_text": colors.HexColor("#2F3338"),
    "bullet": colors.HexColor("#2E8A67"),
    "note_background": colors.HexColor("#EEF5F1"),
    "note_text": colors.HexColor("#274035"),
    "support_background": colors.white,
    "support_border": colors.HexColor("#D6E8DD"),
    "footer_background": colors.HexColor("#2E8A67"),
    "footer_text": colors.white,
    "qr_border": colors.HexColor("#D6E8DD"),
    "meta_background": colors.HexColor("#F1F6F3"),
    "meta_text": colors.HexColor("#355446"),
}

SUPPORT_TITLE = "Support technique | Technical support"
SUPPORT_ITEMS = [
    "www.opticable.ca",
    "support@opticable.ca",
    "514-316-7236 #2",
]
FOOTER_LINE = "Opticable | support@opticable.ca | 514-316-7236 #2"


def _draw_section_title(
    canvas: Canvas,
    x: float,
    y: float,
    width: float,
    title: str,
    fonts: dict[str, str],
) -> None:
    canvas.setFillColor(OPTICABLE_TEMPLATE_01_THEME["section_title_text"])
    canvas.setFont(fonts["bold"], 10)
    canvas.drawString(x, y, title)
    canvas.setStrokeColor(OPTICABLE_TEMPLATE_01_THEME["section_border"])
    canvas.setLineWidth(0.9)
    canvas.line(x, y - 5, x + width, y - 5)


def draw_opticable_template_01(
    canvas: Canvas,
    record: WifiRecord,
    building_name: str,
    qr_path: Path,
    settings: Any,
    fonts: dict[str, str],
    sheet_number: int,
    sheet_total: int,
) -> None:
    theme = OPTICABLE_TEMPLATE_01_THEME
    page_width, page_height = canvas._pagesize
    margin = 24
    radius = 13
    header_height = 88
    header_bottom = page_height - header_height
    panel_width = page_width - (2 * margin)
    label_width = 188
    column_gap = 14
    column_width = (panel_width - column_gap) / 2

    canvas.setTitle(f"{building_name} - {record.ssid}")
    canvas.setAuthor(settings.branding.brand_name)
    canvas.setFillColor(theme["page_background"])
    canvas.rect(0, 0, page_width, page_height, fill=1, stroke=0)

    canvas.setFillColor(theme["header_background"])
    canvas.rect(0, header_bottom, page_width, header_height, fill=1, stroke=0)
    canvas.setFillColor(theme["header_rule"])
    canvas.rect(margin, header_bottom + 10, panel_width, 6, fill=1, stroke=0)
    draw_logo(canvas, settings.branding.logo_path, margin, header_bottom + 28, 220, 40)

    draw_card(
        canvas,
        page_width - margin - 92,
        header_bottom + 8,
        92,
        70,
        colors.white,
        14,
        theme["qr_border"],
    )
    draw_qr(canvas, qr_path, page_width - margin - 80, header_bottom + 14, 66, 58)

    info_y = header_bottom - 86
    draw_label_value_panel(
        canvas,
        margin,
        info_y,
        panel_width,
        78,
        radius,
        label_width,
        fonts,
        theme,
        record.ssid,
        record.password or "",
        label_font_size=9.8,
        ssid_start_size=18,
        ssid_min_size=12,
        password_start_size=18,
        password_min_size=12,
    )

    meta_y = info_y - 38
    meta_width = 150
    for index, value in enumerate((building_name, record.unit_label or "WiFi access", f"Sheet {sheet_number}/{sheet_total}")):
        box_x = margin + (index * (meta_width + 10))
        draw_card(canvas, box_x, meta_y, meta_width, 24, theme["meta_background"], 12)
        canvas.setFillColor(theme["meta_text"])
        canvas.setFont(fonts["bold"], 8.6)
        canvas.drawCentredString(box_x + (meta_width / 2), meta_y + 8, value)

    qr_note_y = meta_y - 54
    draw_card(canvas, margin, qr_note_y, panel_width, 44, theme["note_background"], 12, theme["panel_border"])
    canvas.setFillColor(theme["note_text"])
    draw_paragraph(
        canvas,
        "Scannez le code QR ou utilisez les identifiants ci-dessus pour vous connecter.<br/>"
        "Scan the QR code or use the credentials above to connect.",
        margin + 12,
        qr_note_y + 32,
        panel_width - 24,
        fonts["regular"],
        9.0,
        theme["note_text"],
        leading=10.0,
        bold_fragments=True,
    )

    instructions_y = qr_note_y - 238
    for column_index, (title, items) in enumerate(((FR_TITLE, FR_ITEMS), (EN_TITLE, EN_ITEMS))):
        box_x = margin + (column_index * (column_width + column_gap))
        draw_card(canvas, box_x, instructions_y, column_width, 220, theme["section_background"], radius, theme["section_border"])
        _draw_section_title(canvas, box_x + 14, instructions_y + 200, column_width - 28, title, fonts)
        draw_bullet_list(
            canvas,
            items,
            box_x + 16,
            instructions_y + 182,
            column_width - 32,
            fonts["regular"],
            8.35,
            theme["body_text"],
            theme["bullet"],
            leading=9.3,
            gap=2.0,
        )

    keep_y = instructions_y - 30
    draw_card(canvas, margin, keep_y, panel_width, 24, theme["note_background"], 12)
    canvas.setFillColor(theme["note_text"])
    canvas.setFont(fonts["bold"], 9.1)
    canvas.drawCentredString(margin + (panel_width / 2), keep_y + 8, KEEP_LINE)

    support_y = keep_y - 118
    draw_card(canvas, margin, support_y, panel_width, 104, theme["support_background"], radius, theme["support_border"])
    _draw_section_title(canvas, margin + 14, support_y + 86, panel_width - 28, SUPPORT_TITLE, fonts)
    draw_bullet_list(
        canvas,
        SUPPORT_ITEMS,
        margin + 16,
        support_y + 66,
        panel_width - 32,
        fonts["regular"],
        9.4,
        theme["body_text"],
        theme["bullet"],
        leading=10.1,
        gap=3.2,
    )

    footer_y = support_y - 34
    draw_card(canvas, margin, footer_y, panel_width, 24, theme["footer_background"], 12)
    canvas.setFillColor(theme["footer_text"])
    canvas.setFont(fonts["bold"], 8.8)
    canvas.drawCentredString(margin + (panel_width / 2), footer_y + 8, FOOTER_LINE)
