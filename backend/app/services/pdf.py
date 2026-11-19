from __future__ import annotations

from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "C:/Windows/Fonts/DejaVuSans.ttf",
]

BOLD_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/DejaVuSans-Bold.ttf",
]


def _register_fonts() -> tuple[str, str]:
    regular = None
    bold = None
    for path in FONT_CANDIDATES:
        if Path(path).exists():
            regular = path
            break
    for path in BOLD_CANDIDATES:
        if Path(path).exists():
            bold = path
            break
    if regular:
        pdfmetrics.registerFont(TTFont("SunStay", regular))
        if bold:
            pdfmetrics.registerFont(TTFont("SunStay-Bold", bold))
        else:
            bold = regular
        return "SunStay", "SunStay-Bold"
    return "Helvetica", "Helvetica-Bold"


def money(value) -> str:
    try:
        number = float(value or 0)
    except (TypeError, ValueError):
        number = 0
    return f"{number:,.2f} ₽".replace(",", " ")


def folio_pdf(folio: dict, charges: list[dict], payments: list[dict]) -> bytes:
    regular, bold = _register_fonts()
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=f"Счёт SunStay #{folio.get('folio_id')}",
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "SunStayTitle",
        parent=styles["Title"],
        fontName=bold,
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#123B36"),
        alignment=0,
    )
    body_style = ParagraphStyle(
        "SunStayBody",
        parent=styles["BodyText"],
        fontName=regular,
        fontSize=10,
        leading=14,
    )
    small_style = ParagraphStyle(
        "SunStaySmall",
        parent=body_style,
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#6E746D"),
    )
    table_style = TableStyle(
        [
            ("FONTNAME", (0, 0), (-1, -1), regular),
            ("FONTNAME", (0, 0), (-1, 0), bold),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F3EEE6")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1E2420")),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#E6DED2")),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FBF8F3")]),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]
    )

    story = [
        Paragraph("SunStay", title_style),
        Paragraph("Бутик-отель · Санкт-Петербург, набережная реки Мойки, 12", small_style),
        Spacer(1, 6 * mm),
        Paragraph(f"Счёт Folio #{folio.get('folio_id')} от {str(folio.get('opened_at', ''))[:10]}", body_style),
        Spacer(1, 3 * mm),
    ]

    info_rows = [
        ["Гость", escape(str(folio.get("guest_name") or ""))],
        ["Документ", escape(str(folio.get("document_number") or ""))],
        ["Номер", escape(str(folio.get("room_number") or ""))],
        ["Период", f"{folio.get('checkin_date')} — {folio.get('checkout_date')}"],
        ["Статус", "Открыт" if folio.get("status") == "OPEN" else "Закрыт"],
    ]
    info_table = Table(info_rows, colWidths=[42 * mm, 120 * mm])
    info_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (0, -1), bold),
                ("FONTNAME", (1, 0), (1, -1), regular),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.extend([info_table, Spacer(1, 6 * mm)])

    charge_rows = [["Тип", "Описание", "Дата", "Сумма"]]
    for line in charges:
        charge_rows.append(
            [
                escape(str(line.get("line_type") or "")),
                escape(str(line.get("description") or "")),
                str(line.get("charge_date") or "")[:10],
                money(line.get("amount")),
            ]
        )
    if len(charge_rows) == 1:
        charge_rows.append(["", "Начислений нет", "", money(0)])
    charge_table = Table(charge_rows, colWidths=[24 * mm, 88 * mm, 26 * mm, 32 * mm], repeatRows=1)
    charge_table.setStyle(table_style)
    story.extend([Paragraph("Начисления", ParagraphStyle("H2", parent=body_style, fontName=bold, fontSize=12)), Spacer(1, 2 * mm), charge_table, Spacer(1, 5 * mm)])

    payment_rows = [["Дата", "Способ", "Тип", "Сумма"]]
    for payment in payments:
        payment_rows.append(
            [
                str(payment.get("paid_at") or "")[:10],
                escape(str(payment.get("method") or "")),
                escape(str(payment.get("payment_type") or "")),
                money(payment.get("amount")),
            ]
        )
    if len(payment_rows) == 1:
        payment_rows.append(["", "", "Платежей нет", money(0)])
    payment_table = Table(payment_rows, colWidths=[30 * mm, 40 * mm, 40 * mm, 40 * mm], repeatRows=1)
    payment_table.setStyle(table_style)
    story.extend([Paragraph("Платежи", ParagraphStyle("H3", parent=body_style, fontName=bold, fontSize=12)), Spacer(1, 2 * mm), payment_table, Spacer(1, 6 * mm)])

    totals = [
        ["Начислено", money(folio.get("charged_total"))],
        ["Оплачено", money(folio.get("paid_total"))],
        ["К оплате", money(folio.get("balance"))],
    ]
    totals_table = Table(totals, colWidths=[120 * mm, 42 * mm])
    totals_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), bold),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("LINEABOVE", (0, 2), (-1, 2), 0.8, colors.HexColor("#123B36")),
                ("TOPPADDING", (0, 2), (-1, 2), 6),
            ]
        )
    )
    story.append(totals_table)
    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph("Спасибо, что выбрали SunStay. Документ сформирован автоматически.", small_style))

    doc.build(story)
    return buffer.getvalue()
