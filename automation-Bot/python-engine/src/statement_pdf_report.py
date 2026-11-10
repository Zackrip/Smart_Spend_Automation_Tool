
from io import BytesIO
from datetime import datetime
from decimal import Decimal

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)


def generate_statement_pdf(transactions):

    if not transactions:
        raise ValueError("No transactions available for report.")

    expenses = [
        t for t in transactions
        if t["transaction_type"] == "expense"
    ]

    credits = [
        t for t in transactions
        if t["transaction_type"] == "credit"
    ]

    total_expenses = sum(
        (Decimal(str(t["amount"])) for t in expenses),
        Decimal("0")
    )

    total_credits = sum(
        (Decimal(str(t["amount"])) for t in credits),
        Decimal("0")
    )

    review_count = sum(
        1 for t in transactions if t.get("needs_review", True)
    )

    categories = {}

    for t in expenses:

        category = t.get("category") or "Other"

        if category not in categories:
            categories[category] = {
                "count": 0,
                "amount": Decimal("0")
            }

        categories[category]["count"] += 1
        categories[category]["amount"] += Decimal(
            str(t["amount"])
        )

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=12 * mm,
        leftMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=15 * mm
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        textColor=colors.HexColor("#17365D"),
        fontSize=20
    )

    story = []

    story.append(Paragraph("SMARTSPEND AI", title_style))
    story.append(
        Paragraph(
            "Transaction Statement Report",
            styles["Heading2"]
        )
    )

    story.append(Spacer(1, 8))

    story.append(Paragraph(
        f"Generated: {datetime.now().strftime('%d %b %Y, %I:%M %p')}",
        styles["Normal"]
    ))

    # Overview
    story.append(Spacer(1, 12))
    story.append(Paragraph(
        "1. Transaction Overview",
        styles["Heading2"]
    ))

    overview = [
        ["Total Transactions", "Total Expenses",
         "Total Credits", "Needs Review"],
        [
            str(len(transactions)),
            f"Rs. {total_expenses:,.2f}",
            f"Rs. {total_credits:,.2f}",
            str(review_count)
        ]
    ]

    table = Table(overview, colWidths=[65 * mm] * 4)

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0),
         colors.HexColor("#17365D")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, 1), (-1, 1),
         colors.HexColor("#EAF0F7")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("PADDING", (0, 0), (-1, -1), 8)
    ]))

    story.append(table)

    # Category summary
    story.append(Spacer(1, 15))
    story.append(Paragraph(
        "2. Category-wise Expenses",
        styles["Heading2"]
    ))

    category_data = [
        ["Category", "Transaction Count", "Total Amount"]
    ]

    for category, values in sorted(
        categories.items(),
        key=lambda x: x[1]["amount"],
        reverse=True
    ):
        category_data.append([
            category,
            str(values["count"]),
            f"Rs. {values['amount']:,.2f}"
        ])

    category_data.append([
        "TOTAL",
        str(len(expenses)),
        f"Rs. {total_expenses:,.2f}"
    ])

    category_table = Table(
        category_data,
        colWidths=[90 * mm, 60 * mm, 70 * mm],
        repeatRows=1
    )

    category_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0),
         colors.HexColor("#17365D")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ALIGN", (1, 1), (-1, -1), "CENTER"),
        ("PADDING", (0, 0), (-1, -1), 7)
    ]))

    story.append(category_table)

    # Complete transactions
    story.append(Spacer(1, 15))
    story.append(Paragraph(
        "3. Complete Transaction Details",
        styles["Heading2"]
    ))

    transaction_data = [[
        "Date", "Merchant", "Amount",
        "Type", "Category", "Review"
    ]]

    for t in transactions:

        date_value = t.get("transaction_date")

        if hasattr(date_value, "strftime"):
            date_value = date_value.strftime("%d-%m-%Y")

        transaction_data.append([
            str(date_value or ""),
            Paragraph(
                str(t.get("merchant") or "Unknown"),
                ParagraphStyle(
                    "Merchant",
                    parent=styles["Normal"],
                    fontSize=7
                )
            ),
            f"Rs. {Decimal(str(t['amount'])):,.2f}",
            str(t["transaction_type"]).title(),
            str(t.get("category") or "Other"),
            "Yes" if t.get("needs_review", True) else "No"
        ])

    transaction_table = Table(
        transaction_data,
        colWidths=[
            28 * mm, 75 * mm, 35 * mm,
            32 * mm, 45 * mm, 25 * mm
        ],
        repeatRows=1
    )

    transaction_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0),
         colors.HexColor("#17365D")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING", (0, 0), (-1, -1), 6),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#F4F6F8")])
    ]))

    story.append(transaction_table)

    def footer(canvas, document):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.drawString(
            12 * mm, 7 * mm,
            "SmartSpend AI | Transaction Report"
        )
        canvas.drawRightString(
            landscape(A4)[0] - 12 * mm,
            7 * mm,
            f"Page {document.page}"
        )
        canvas.restoreState()

    doc.build(
        story,
        onFirstPage=footer,
        onLaterPages=footer
    )

    buffer.seek(0)

    return buffer
