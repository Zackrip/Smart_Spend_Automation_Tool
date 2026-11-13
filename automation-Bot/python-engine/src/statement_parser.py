
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from io import BytesIO

import pdfplumber


DATE_PATTERN = re.compile(
    r"([A-Z][a-z]{2}\s+\d{1,2},\s+\d{4})"
)

TIME_PATTERN = re.compile(
    r"(\d{1,2}:\d{2}\s*(?:am|pm))",
    re.IGNORECASE,
)

AMOUNT_PATTERN = re.compile(
    r"₹\s*([\d,]+(?:\.\d{1,2})?)"
)

TRANSACTION_ID_PATTERN = re.compile(
    r"Transaction ID\s+([A-Za-z0-9]+)",
    re.IGNORECASE,
)

UTR_PATTERN = re.compile(
    r"UTR No\.?\s+([A-Za-z0-9]+)",
    re.IGNORECASE,
)

HEADER_ROW_PATTERN = re.compile(
    r"^\s*(?P<date>[A-Z][a-z]{2}\s+\d{1,2},\s+\d{4})\s+"
    r"(?P<description>.*?)\s+"
    r"(?P<direction>DEBIT|CREDIT)\s+"
    r"₹\s*(?P<amount>[\d,]+(?:\.\d{1,2})?)\s*$",
    re.IGNORECASE,
)

METADATA_END_PATTERN = (
    r"Paid by|Credited to|CREDIT|DEBIT|"
    r"Transaction ID|UTR No\.?"
)


def _normalise_description(description):
    """Normalize whitespace and remove trailing decorative symbols."""
    if not description:
        return ""

    return (
        re.sub(r"\s+", " ", description)
        .strip()
        .rstrip("♥❤")
        .strip()
    )


def _identify_counterparty(description):
    """
    Extract a counterparty and identify recognizable transaction wording.

    This function does not decide whether a person is a friend,
    family member, or merchant.
    """
    description = _normalise_description(description)

    patterns = (
        (
            r"^(?:Paid to|Payment to)\s+(.+)$",
            None,
        ),
        (
            r"^Received from\s+(.+)$",
            "personal_or_external_credit",
        ),
        (
            r"^Cashback from\s+(.+)$",
            "cashback",
        ),
        (
            r"^(?:Refund from|Refund for)\s+(.+)$",
            "refund",
        ),
        (
            r"^(?:Reversal from|Payment reversal)\s+(.+)$",
            "refund",
        ),
        (
            r"^(?:Top[- ]?up\s+Wallet|Wallet\s+Top[- ]?up|"
            r"Added to Wallet)$",
            "wallet_top_up",
        ),
    )

    for pattern, subtype in patterns:
        match = re.match(pattern, description, re.IGNORECASE)

        if match:
            if match.lastindex:
                counterparty = _normalise_description(match.group(1))
            elif subtype == "wallet_top_up":
                counterparty = "Wallet"
            else:
                counterparty = description

            return counterparty, subtype

    bill_patterns = (
        (r"^Electricity bill paid\b", "Electricity Bill"),
        (r"^Insurance Success\b", "Insurance"),
        (r"^Mobile bill paid\b", "Mobile Bill"),
        (r"^Mobile recharged\b", "Mobile Recharge"),
        (r"^Credit card bill paid\b", "Credit Card Bill"),
        (r"^Broadband bill paid\b", "Broadband Bill"),
        (r"^DTH recharge\b", "DTH Recharge"),
    )

    for pattern, counterparty in bill_patterns:
        if re.search(pattern, description, re.IGNORECASE):
            return counterparty, "bill_payment"

    return description or "Unknown", "unclassified_description"


def extract_payment_metadata(block):
    """Extract payment source and credited destination separately."""

    paid_by_match = re.search(
        rf"\bPaid by\s+(.+?)"
        rf"(?=\s+(?:{METADATA_END_PATTERN})\b|$)",
        block,
        re.IGNORECASE | re.DOTALL,
    )

    credited_to_match = re.search(
        rf"\bCredited to\s+(.+?)"
        rf"(?=\s+(?:{METADATA_END_PATTERN})\b|$)",
        block,
        re.IGNORECASE | re.DOTALL,
    )

    payment_source = (
        _normalise_description(paid_by_match.group(1))
        if paid_by_match
        else None
    )

    credited_to = (
        _normalise_description(credited_to_match.group(1))
        if credited_to_match
        else None
    )

    return {
        "payment_source": payment_source,
        "credited_to": credited_to,
    }


def _extract_description(block):
    """Extract transaction narration without trailing payment metadata."""

    detail_match = re.search(
        r"((?:Paid to|Payment to|Received from|Cashback from|"
        r"Refund from|Refund for|Reversal from|Payment reversal)"
        r"\s+.+?)"
        rf"(?=\s+(?:{METADATA_END_PATTERN})\b|$)",
        block,
        re.IGNORECASE | re.DOTALL,
    )

    if detail_match:
        return _normalise_description(detail_match.group(1))

    topup_match = re.search(
        r"\b(?:Top[- ]?up\s+Wallet|Wallet\s+Top[- ]?up|"
        r"Added to Wallet)\b",
        block,
        re.IGNORECASE,
    )

    if topup_match:
        return _normalise_description(topup_match.group(0))

    bill_patterns = (
        r"Electricity bill paid[^\n]*",
        r"Insurance Success[^\n]*",
        r"Mobile bill paid[^\n]*",
        r"Mobile recharged[^\n]*",
        r"Credit card bill paid[^\n]*",
        r"Broadband bill paid[^\n]*",
        r"DTH recharge[^\n]*",
    )

    for pattern in bill_patterns:
        match = re.search(pattern, block, re.IGNORECASE)

        if match:
            return _normalise_description(match.group(0))

    return ""


def extract_phonepe_transactions(pdf_bytes: bytes):
    """Extract PhonePe transactions from PDF bytes."""

    transactions = []

    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):

            page_text = page.extract_text() or ""
            lines = page_text.splitlines()
            current_block = []

            for line in lines:

                if DATE_PATTERN.search(line):

                    if current_block:
                        transaction = parse_transaction_block(
                            current_block,
                            page_number,
                        )

                        if transaction:
                            transactions.append(transaction)

                    current_block = [line]

                elif current_block:
                    current_block.append(line)

            if current_block:
                transaction = parse_transaction_block(
                    current_block,
                    page_number,
                )

                if transaction:
                    transactions.append(transaction)

    return transactions


def parse_transaction_block(lines, page_number):
    """Parse one PhonePe transaction block."""

    if not lines:
        return None

    block = "\n".join(lines)
    first_line = lines[0]

    row_match = HEADER_ROW_PATTERN.match(first_line)

    if row_match:

        date_text = row_match.group("date")
        description = _normalise_description(
            row_match.group("description")
        )
        direction = row_match.group("direction").upper()
        amount_text = row_match.group("amount")

    else:

        date_match = DATE_PATTERN.search(block)
        amount_match = AMOUNT_PATTERN.search(block)

        if not date_match or not amount_match:
            return None

        direction_match = re.search(
            r"\b(CREDIT|DEBIT)\b",
            block,
            re.IGNORECASE,
        )

        if not direction_match:
            return None

        date_text = date_match.group(1)
        direction = direction_match.group(1).upper()
        amount_text = amount_match.group(1)

        description = _extract_description(block)

        if not description:
            description = _normalise_description(
                first_line.replace(date_text, "", 1)
            )

    try:
        transaction_date = datetime.strptime(
            date_text,
            "%b %d, %Y",
        ).date().isoformat()

        amount = Decimal(amount_text.replace(",", ""))

    except (ValueError, InvalidOperation):
        return None

    counterparty, subtype = _identify_counterparty(description)

    time_match = TIME_PATTERN.search(block)

    transaction_time = None

    if time_match:
        try:
            transaction_time = datetime.strptime(
                time_match.group(1).upper().replace("  ", " "),
                "%I:%M %p",
            ).strftime("%H:%M:%S")
        except ValueError:
            transaction_time = None

    transaction_id_match = TRANSACTION_ID_PATTERN.search(block)
    utr_match = UTR_PATTERN.search(block)

    metadata = extract_payment_metadata(block)

    # PhonePe PDF statements explicitly print an AUTOPAY badge for mandate-based
    # debits. Do not infer Auto Pay from merchant names or recurring amounts.
    is_autopay = bool(re.search(r"\bAUTOPAY\b", block, re.IGNORECASE))
    payment_mode = "autopay" if is_autopay else "unknown"

    return {
        "transaction_date": transaction_date,
        "transaction_time": transaction_time,

        # Extracted counterparty, not a confirmed merchant/person identity.
        "merchant": counterparty,

        # Preserve the original transaction narration.
        "transaction_description": description,

        "transaction_subtype": subtype,

        # Decimal avoids floating-point precision errors.
        "amount": amount,

        "transaction_type": (
            "credit" if direction == "CREDIT" else "expense"
        ),

        "payment_source": metadata["payment_source"],
        "credited_to": metadata["credited_to"],
        "payment_mode": payment_mode,
        "is_autopay": True if is_autopay else None,
        "autopay_detection_source": "phonepe_pdf_badge" if is_autopay else None,

        "transaction_id": (
            transaction_id_match.group(1)
            if transaction_id_match
            else None
        ),

        "utr": (
            utr_match.group(1)
            if utr_match
            else None
        ),

        "source": "phonepe_statement",
        "page_number": page_number,
    }
