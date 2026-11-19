from __future__ import annotations

from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .pdf import _register_fonts, money


def booking_voucher_pdf(booking: dict, guest: dict) -> bytes:
    regular, bold = _register_fonts()
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=f"Ваучер SunStay #{booking.get('booking_id')}",
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "SunStayTitle",
        parent=styles["Title"],
        fontName=bold,
        fontSize=22,
        leading=26,
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
    subtitle_style = ParagraphStyle(
        "SunStaySubtitle",
        parent=body_style,
        fontName=bold,
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#1E2420"),
    )

    story = [
        Paragraph("SunStay", title_style),
        Paragraph("Ваучер на проживание", subtitle_style),
        Paragraph("Бутик-отель · Санкт-Петербург, набережная реки Мойки, 12", small_style),
        Spacer(1, 6 * mm),
    ]

    info_rows = [
        ["Гость", escape(str(guest.get("full_name") or booking.get("guest_name") or ""))],
        ["Бронь", f"#{booking.get('booking_id')}"],
        ["Номер", escape(str(booking.get("room_number") or ""))],
        ["Категория", escape(str(booking.get("room_type") or ""))],
        ["Заезд", str(booking.get("checkin_date") or "")],
        ["Выезд", str(booking.get("checkout_date") or "")],
        ["Гостей", str((booking.get("adults") or 0) + (booking.get("children") or 0))],
        ["Статус", str(booking.get("status") or "")],
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

    if booking.get("price_per_night") is not None:
        nights = _nights(booking.get("checkin_date"), booking.get("checkout_date"))
        total = (float(booking.get("price_per_night") or 0) or 0) * nights
        price_rows = [
            ["Тариф", str(booking.get("rate_name") or "")],
            ["Цена за ночь", money(booking.get("price_per_night"))],
            ["Ночей", str(nights)],
            ["Итого", money(total)],
        ]
        price_table = Table(price_rows, colWidths=[100 * mm, 62 * mm])
        price_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, -1), regular),
                    ("FONTNAME", (0, -1), (-1, -1), bold),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("LINEABOVE", (0, -1), (-1, -1), 0.8, colors.HexColor("#123B36")),
                ]
            )
        )
        story.extend([Paragraph("Стоимость", subtitle_style), Spacer(1, 2 * mm), price_table, Spacer(1, 6 * mm)])

    story.append(Paragraph("Предъявите ваучер при заселении. Спасибо, что выбрали SunStay.", small_style))

    doc.build(story)
    return buffer.getvalue()


def _nights(checkin: str | None, checkout: str | None) -> int:
    if not checkin or not checkout:
        return 0
    from datetime import datetime

    try:
        start = datetime.fromisoformat(str(checkin)[:10])
        end = datetime.fromisoformat(str(checkout)[:10])
    except ValueError:
        return 0
    return max(0, (end - start).days)
