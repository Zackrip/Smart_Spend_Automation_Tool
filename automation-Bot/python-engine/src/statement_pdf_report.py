"""Paisora Dark Executive PhonePe statement PDF generator.

Dependencies: reportlab, matplotlib (matplotlib is optional; charts gracefully fall back).
The function signature remains generate_statement_pdf(transactions), so the existing API import
can continue to call it without changes.
"""
from __future__ import annotations
from collections import defaultdict
from datetime import datetime
from io import BytesIO
from pathlib import Path
import os

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
    KeepTogether, HRFlowable
)

NAVY = colors.HexColor("#0B1220")
PANEL = colors.HexColor("#111C2E")
PANEL2 = colors.HexColor("#17243A")
GREEN = colors.HexColor("#20C997")
WHITE = colors.HexColor("#F4F7FB")
MUTED = colors.HexColor("#9AA8BC")
RED = colors.HexColor("#FF6B6B")
GOLD = colors.HexColor("#D7B56D")

def _register_fonts():
    """Register a Unicode TTF where available; use Helvetica as a safe fallback."""
    candidates = [
        ("Paisora", [
            os.environ.get("PAISORA_FONT"),
            r"C:\Windows\Fonts\arial.ttf",
            r"C:\Windows\Fonts\segoeui.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        ]),
        ("Paisora-Bold", [
            r"C:\Windows\Fonts\arialbd.ttf",
            r"C:\Windows\Fonts\segoeuib.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
        ])
    ]
    registered = {}
    for name, paths in candidates:
        for path in paths:
            if path and Path(path).is_file():
                try:
                    pdfmetrics.registerFont(TTFont(name, path))
                    registered[name] = True
                    break
                except Exception:
                    pass
    if "Paisora" in registered:
        regular = "Paisora"
        bold = "Paisora-Bold" if "Paisora-Bold" in registered else "Paisora"
    else:
        regular, bold = "Helvetica", "Helvetica-Bold"
    return regular, bold

FONT, FONT_BOLD = _register_fonts()

def _value(tx, *keys, default=None):
    for key in keys:
        if isinstance(tx, dict) and tx.get(key) not in (None, ""):
            return tx.get(key)
    return default

def _amount(tx):
    raw = _value(tx, "amount", "transaction_amount", "value", default=0)
    try:
        return abs(float(str(raw).replace(",", "").replace("₹", "").strip()))
    except (TypeError, ValueError):
        return 0.0

def _date_text(tx):
    raw = _value(tx, "date", "transaction_date", "datetime", "transaction_time", default="")
    if isinstance(raw, datetime):
        return raw.strftime("%d %b %Y")
    return str(raw)[:20] if raw else "—"

def _kind(tx):
    raw = str(_value(tx, "type", "transaction_type", "direction", default="")).lower()
    if any(x in raw for x in ("credit", "received", "cashback", "refund")):
        return "Credit"
    if any(x in raw for x in ("debit", "paid", "sent", "payment", "expense")):
        return "Expense"
    # Infer from common signed amount fields if available.
    signed = _value(tx, "signed_amount", "amount_signed")
    try:
        return "Credit" if signed is not None and float(signed) > 0 else "Expense"
    except (TypeError, ValueError):
        return "Expense"

def _money(value):
    return f"₹{value:,.2f}"

def _make_styles():
    return {
        "cover_kicker": ParagraphStyle("cover_kicker", fontName=FONT_BOLD, fontSize=9, leading=13, textColor=GREEN, spaceAfter=12),
        "cover_title": ParagraphStyle("cover_title", fontName=FONT_BOLD, fontSize=31, leading=37, textColor=WHITE),
        "cover_sub": ParagraphStyle("cover_sub", fontName=FONT, fontSize=11, leading=17, textColor=MUTED),
        "h1": ParagraphStyle("h1", fontName=FONT_BOLD, fontSize=19, leading=24, textColor=WHITE, spaceAfter=5),
        "h2": ParagraphStyle("h2", fontName=FONT_BOLD, fontSize=10, leading=13, textColor=GREEN),
        "body": ParagraphStyle("body", fontName=FONT, fontSize=8.5, leading=12, textColor=WHITE),
        "muted": ParagraphStyle("muted", fontName=FONT, fontSize=8, leading=11, textColor=MUTED),
        "small": ParagraphStyle("small", fontName=FONT, fontSize=7, leading=9, textColor=MUTED),
        "table_head": ParagraphStyle("table_head", fontName=FONT_BOLD, fontSize=7.2, leading=9, textColor=GREEN),
        "table_cell": ParagraphStyle("table_cell", fontName=FONT, fontSize=7, leading=9, textColor=WHITE),
        "table_right": ParagraphStyle("table_right", fontName=FONT, fontSize=7, leading=9, textColor=WHITE, alignment=TA_RIGHT),
    }

def _dark_page(canvas, doc):
    canvas.saveState()
    w, h = A4
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, w, h, fill=1, stroke=0)
    if doc.page > 1:
        canvas.setStrokeColor(PANEL2)
        canvas.setLineWidth(0.6)
        canvas.line(17*mm, 15*mm, w-17*mm, 15*mm)
        canvas.setFont(FONT, 7)
        canvas.setFillColor(MUTED)
        canvas.drawString(17*mm, 10*mm, "PAISORA  •  PRIVATE FINANCIAL REPORT")
        canvas.drawRightString(w-17*mm, 10*mm, f"{doc.page}")
    canvas.restoreState()

def _card(label, value, styles, accent=GREEN):
    label_p = Paragraph(label.upper(), ParagraphStyle("cardlabel", parent=styles["small"], textColor=MUTED, fontName=FONT_BOLD))
    value_p = Paragraph(value, ParagraphStyle("cardvalue", fontName=FONT_BOLD, fontSize=15, leading=19, textColor=accent))
    t = Table([[label_p], [value_p]], colWidths=[39*mm], rowHeights=[8*mm, 13*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), PANEL),
        ("BOX", (0,0), (-1,-1), 0.6, PANEL2),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ]))
    return t

def _chart_image(category_totals):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        labels = list(category_totals.keys()) or ["No data"]
        values = list(category_totals.values()) or [0]
        fig, ax = plt.subplots(figsize=(7.2, 3.0), dpi=160)
        fig.patch.set_facecolor("#0B1220")
        ax.set_facecolor("#0B1220")
        bars = ax.barh(labels, values, color="#20C997")
        ax.tick_params(colors="#D8E1ED", labelsize=8)
        ax.spines[:].set_visible(False)
        ax.xaxis.label.set_color("#9AA8BC")
        ax.set_xlabel("Amount (INR)", color="#9AA8BC", fontsize=8)
        ax.grid(axis="x", color="#26364D", alpha=0.7)
        ax.set_axisbelow(True)
        fig.tight_layout()
        buffer = BytesIO()
        fig.savefig(buffer, format="png", facecolor=fig.get_facecolor(), bbox_inches="tight")
        plt.close(fig)
        buffer.seek(0)
        from reportlab.platypus import Image
        return Image(buffer, width=170*mm, height=72*mm)
    except Exception:
        return Paragraph("Chart unavailable — install matplotlib to enable category visualisation.", 
                         ParagraphStyle("chartfallback", fontName=FONT, fontSize=8, textColor=MUTED))

def generate_statement_pdf(transactions, branding="Paisora"):
    """Return a BytesIO PDF with cover page, dashboard, analysis and full transaction table."""
    transactions = list(transactions or [])
    styles = _make_styles()
    expenses = sum(_amount(t) for t in transactions if _kind(t) == "Expense")
    credits = sum(_amount(t) for t in transactions if _kind(t) == "Credit")
    categories = defaultdict(float)
    for tx in transactions:
        if _kind(tx) == "Expense":
            categories[str(_value(tx, "category", default="Other"))] += _amount(tx)
    autopay_count = sum(1 for tx in transactions if _value(tx, "payment_mode", default="unknown") == "autopay")
    review_count = sum(
        1 for tx in transactions
        if bool(_value(tx, "needs_review", "review_required", default=False))
        or str(_value(tx, "classification_method", default="")).lower() in ("unknown", "needs_review")
    )
    period_values = [_date_text(t) for t in transactions if _date_text(t) != "—"]
    period = f"{min(period_values)}  —  {max(period_values)}" if period_values else "Period not available"
    generated = datetime.now().strftime("%d %B %Y")

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=17*mm, leftMargin=17*mm,
                            topMargin=18*mm, bottomMargin=22*mm, title=f"{branding} | PhonePe Statement")
    story = []

    # PAGE 1 — premium cover
    story += [
        Spacer(1, 24*mm),
        Paragraph("PERSONAL FINANCE  /  STATEMENT INSIGHTS", styles["cover_kicker"]),
        Spacer(1, 8*mm),
        Paragraph(branding.upper(), styles["cover_title"]),
        Spacer(1, 3*mm),
        Paragraph("PhonePe Transaction Report", ParagraphStyle("cover2", fontName=FONT_BOLD, fontSize=19, leading=25, textColor=GREEN)),
        Spacer(1, 7*mm),
        HRFlowable(width="100%", thickness=1.2, color=GREEN),
        Spacer(1, 8*mm),
        Paragraph("A clearer view of where your money moves.", styles["cover_sub"]),
        Spacer(1, 28*mm),
    ]
    cover_grid = Table([
        [Paragraph("STATEMENT PERIOD", styles["h2"]), Paragraph("GENERATED ON", styles["h2"])],
        [Paragraph(period, styles["body"]), Paragraph(generated, styles["body"])],
        [Paragraph("TRANSACTIONS ANALYSED", styles["h2"]), Paragraph("REPORT TYPE", styles["h2"])],
        [Paragraph(str(len(transactions)), styles["body"]), Paragraph("Expense & credit summary", styles["body"])]
    ], colWidths=[83*mm, 83*mm], rowHeights=[8*mm, 13*mm, 8*mm, 13*mm])
    cover_grid.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), PANEL),
        ("BOX", (0,0), (-1,-1), 0.8, PANEL2),
        ("INNERGRID", (0,0), (-1,-1), 0.4, PANEL2),
        ("LEFTPADDING", (0,0), (-1,-1), 9),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ]))
    story += [cover_grid, Spacer(1, 30*mm),
              Paragraph("CONFIDENTIAL • FOR PERSONAL USE", styles["small"]),
              PageBreak()]

    # PAGE 2 — overview
    story += [
        Paragraph("Financial overview", styles["h1"]),
        Paragraph(
            f"A snapshot of the transactions included in this statement.  Auto Pay detected: {autopay_count}",
            styles["muted"],
        ),
        Spacer(1, 7*mm)
    ]
    cards = [
        _card("Total expenses", _money(expenses), styles, RED),
        _card("Total credits", _money(credits), styles, GREEN),
        _card("Transactions", str(len(transactions)), styles, WHITE),
        _card("Needs review", str(review_count), styles, GOLD),
    ]
    card_table = Table([cards[:2], cards[2:]], colWidths=[83*mm, 83*mm], rowHeights=[27*mm, 27*mm])
    card_table.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"MIDDLE"),("LEFTPADDING",(0,0),(-1,-1),0),
                                    ("RIGHTPADDING",(0,0),(-1,-1),5),("TOPPADDING",(0,0),(-1,-1),4),
                                    ("BOTTOMPADDING",(0,0),(-1,-1),4)]))
    story += [card_table, Spacer(1, 8*mm),
              Paragraph("Category-wise expenses", styles["h2"]), Spacer(1, 3*mm)]
    sorted_categories = dict(sorted(categories.items(), key=lambda x: x[1], reverse=True))
    story.append(_chart_image(sorted_categories))
    story += [Spacer(1, 3*mm), Paragraph("Top spending categories", styles["h2"]), Spacer(1, 2*mm)]
    cat_rows = [[Paragraph("CATEGORY", styles["table_head"]), Paragraph("EXPENSE", styles["table_head"])]]
    for cat, amount in list(sorted_categories.items())[:8]:
        cat_rows.append([Paragraph(str(cat), styles["table_cell"]),
                         Paragraph(_money(amount), styles["table_right"])])
    if len(cat_rows) == 1:
        cat_rows.append([Paragraph("No expense records", styles["muted"]), Paragraph("—", styles["muted"])])
    cat_table = Table(cat_rows, colWidths=[120*mm, 46*mm], repeatRows=1)
    cat_table.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),PANEL2),("BACKGROUND",(0,1),(-1,-1),PANEL),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[PANEL, NAVY]),("LINEBELOW",(0,0),(-1,0),0.6,GREEN),
        ("LEFTPADDING",(0,0),(-1,-1),7),("RIGHTPADDING",(0,0),(-1,-1),7),
        ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
    ]))
    story += [cat_table, PageBreak()]

    # PAGE 3+ — transaction details
    story += [
        Paragraph("Transaction details", styles["h1"]),
        Paragraph("All parsed transactions are listed below. Unknown classifications are flagged for review.", styles["muted"]),
        Spacer(1, 5*mm)
    ]
    headers = ["DATE", "MERCHANT / DESCRIPTION", "AMOUNT", "TYPE", "CATEGORY", "PAYMENT MODE", "REVIEW"]
    rows = [[Paragraph(h, styles["table_head"]) for h in headers]]
    for tx in transactions:
        merchant = str(_value(tx, "merchant", "counterparty", "name", "description", default="Unknown"))
        merchant = merchant.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        category = str(_value(tx, "category", default="Other"))
        needs_review = bool(_value(tx, "needs_review", "review_required", default=False))
        payment_mode = str(_value(tx, "payment_mode", default="unknown")).replace("_", " ").upper()
        rows.append([
            Paragraph(_date_text(tx).replace("&", "&amp;"), styles["table_cell"]),
            Paragraph(merchant[:65], styles["table_cell"]),
            Paragraph(_money(_amount(tx)), styles["table_right"]),
            Paragraph(_kind(tx), styles["table_cell"]),
            Paragraph(category, styles["table_cell"]),
            Paragraph(payment_mode, styles["table_cell"]),
            Paragraph("Review" if needs_review else "OK",
                      ParagraphStyle("reviewcell", fontName=FONT_BOLD, fontSize=7, textColor=GOLD if needs_review else GREEN))
        ])
    if len(rows) == 1:
        rows.append([Paragraph("No transactions found.", styles["muted"])] + [Paragraph("", styles["muted"])]*6)
    table = Table(rows, colWidths=[19*mm, 43*mm, 22*mm, 15*mm, 22*mm, 25*mm, 20*mm], repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),PANEL2),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[PANEL, NAVY]),
        ("LINEBELOW",(0,0),(-1,0),0.8,GREEN),
        ("LINEBELOW",(0,1),(-1,-1),0.25,PANEL2),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("LEFTPADDING",(0,0),(-1,-1),5),("RIGHTPADDING",(0,0),(-1,-1),5),
        ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
    ]))
    story.append(table)

    doc.build(story, onFirstPage=_dark_page, onLaterPages=_dark_page)
    buffer.seek(0)
    return buffer
