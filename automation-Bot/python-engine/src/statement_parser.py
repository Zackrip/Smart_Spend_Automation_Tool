import re
from datetime import datetime
from io import BytesIO

import pdfplumber


DATE_PATTERN = re.compile(r"([A-Z][a-z]{2}\s+\d{1,2},\s+\d{4})")
TIME_PATTERN = re.compile(r"(\d{1,2}:\d{2}\s*(?:am|pm))", re.IGNORECASE)
AMOUNT_PATTERN = re.compile(r"₹\s*([\d,]+(?:\.\d{1,2})?)")
TRANSACTION_ID_PATTERN = re.compile(r"Transaction ID\s+([A-Za-z0-9]+)", re.IGNORECASE)
UTR_PATTERN = re.compile(r"UTR No\.?\s+([A-Za-z0-9]+)", re.IGNORECASE)

# PhonePe puts the date, description, direction and amount on one row.
HEADER_ROW_PATTERN = re.compile(
    r"^\s*(?P<date>[A-Z][a-z]{2}\s+\d{1,2},\s+\d{4})\s+"
    r"(?P<description>.*?)\s+"
    r"(?P<direction>DEBIT|CREDIT)\s+"
    r"₹\s*(?P<amount>[\d,]+(?:\.\d{1,2})?)\s*$",
    re.IGNORECASE,
)


def extract_phonepe_transactions(pdf_bytes: bytes):
    """Extract PhonePe transactions while preserving the original description."""
    transactions = []

    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            page_text = page.extract_text() or ""
            lines = page_text.splitlines()
            current_block = []

            for line in lines:
                if DATE_PATTERN.search(line):
                    if current_block:
                        transaction = parse_transaction_block(current_block, page_number)
                        if transaction:
                            transactions.append(transaction)
                    current_block = [line]
                elif current_block:
                    current_block.append(line)

            if current_block:
                transaction = parse_transaction_block(current_block, page_number)
                if transaction:
                    transactions.append(transaction)

    return transactions


def _normalise_description(description):
    return re.sub(r"\s+", " ", description).strip().rstrip("♥❤").strip()


def _identify_counterparty(description):
    """Return a useful counterparty and a transaction subtype from PhonePe wording."""
    description = _normalise_description(description)

    patterns = (
        (r"^(?:Paid to|Payment to)\s+(.+)$", None),
        (r"^Received from\s+(.+)$", "personal_or_external_credit"),
        (r"^Cashback from\s+(.+)$", "cashback"),
        (r"^Top[- ]?up\s+Wallet$", "wallet_top_up"),
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

    # PhonePe sometimes describes bill payments without "Paid to".
    bill_patterns = (
        (r"^Electricity bill paid\b", "Electricity Bill"),
        (r"^Insurance Success\b", "Insurance"),
        (r"^Mobile bill paid\b", "Mobile Bill"),
        (r"^Mobile recharged\b", "Mobile Recharge"),
        (r"^Credit card bill paid\b", "Credit Card Bill"),
    )
    for pattern, counterparty in bill_patterns:
        if re.search(pattern, description, re.IGNORECASE):
            return counterparty, "bill_payment"

    # Preserve unfamiliar descriptions instead of silently replacing them with Unknown.
    return description or "Unknown", "unclassified_description"


def parse_transaction_block(lines, page_number):
    block = "\n".join(lines)
    first_line = lines[0] if lines else ""

    # Prefer the structured transaction row; it contains the full description.
    row_match = HEADER_ROW_PATTERN.match(first_line)
    if row_match:
        date_text = row_match.group("date")
        description = _normalise_description(row_match.group("description"))
        direction = row_match.group("direction").upper()
        amount_text = row_match.group("amount")
    else:
        # Fallback for PDF layouts where columns wrap onto separate lines.
        date_match = DATE_PATTERN.search(block)
        amount_match = AMOUNT_PATTERN.search(block)
        if not date_match or not amount_match:
            return None

        direction_match = re.search(r"\b(CREDIT|DEBIT)\b", block, re.IGNORECASE)
        if not direction_match:
            return None

        date_text = date_match.group(1)
        direction = direction_match.group(1).upper()
        amount_text = amount_match.group(1)

        detail_match = re.search(
            r"((?:Paid to|Payment to|Received from|Cashback from)\s+.+?)"
            r"(?=\s+(?:CREDIT|DEBIT)\b|$)",
            block,
            re.IGNORECASE | re.DOTALL,
        )
        description = _normalise_description(detail_match.group(1)) if detail_match else ""

        if not description:
            topup_match = re.search(r"\bTop[- ]?up\s+Wallet\b", block, re.IGNORECASE)
            if topup_match:
                description = "Top-up Wallet"
            else:
                # Keep any identifiable text from the transaction's first row.
                description = _normalise_description(first_line.replace(date_text, "", 1))

    transaction_date = datetime.strptime(date_text, "%b %d, %Y").date().isoformat()
    amount = float(amount_text.replace(",", ""))
    counterparty, subtype = _identify_counterparty(description)

    time_match = TIME_PATTERN.search(block)
    transaction_time = None
    if time_match:
        transaction_time = datetime.strptime(
            time_match.group(1).upper(), "%I:%M %p"
        ).strftime("%H:%M:%S")

    transaction_id_match = TRANSACTION_ID_PATTERN.search(block)
    utr_match = UTR_PATTERN.search(block)

    return {
        "transaction_date": transaction_date,
        "transaction_time": transaction_time,
        "merchant": counterparty,
        "transaction_description": description,
        "transaction_subtype": subtype,
        "amount": amount,
        "transaction_type": "credit" if direction == "CREDIT" else "expense",
        "transaction_id": transaction_id_match.group(1) if transaction_id_match else None,
        "utr": utr_match.group(1) if utr_match else None,
        "source": "phonepe_statement",
        "page_number": page_number,
    }
