import re
from datetime import datetime
from io import BytesIO

import pdfplumber


DATE_PATTERN = re.compile(
    r"([A-Z][a-z]{2}\s+\d{1,2},\s+\d{4})"
)

TIME_PATTERN = re.compile(
    r"(\d{1,2}:\d{2}\s*(?:am|pm))",
    re.IGNORECASE
)

AMOUNT_PATTERN = re.compile(
    r"₹\s*([\d,]+(?:\.\d{1,2})?)"
)

TRANSACTION_ID_PATTERN = re.compile(
    r"Transaction ID\s+([A-Za-z0-9]+)",
    re.IGNORECASE
)

UTR_PATTERN = re.compile(
    r"UTR No\.?\s+([A-Za-z0-9]+)",
    re.IGNORECASE
)


def extract_phonepe_transactions(pdf_bytes: bytes):

    transactions = []

    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:

        for page_number, page in enumerate(pdf.pages, start=1):

            page_text = page.extract_text() or ""

            lines = page_text.splitlines()

            current_block = []

            for line in lines:

                # A transaction starts with a date.
                if DATE_PATTERN.search(line):

                    if current_block:
                        transaction = parse_transaction_block(
                            current_block,
                            page_number
                        )

                        if transaction:
                            transactions.append(transaction)

                    current_block = [line]

                elif current_block:
                    current_block.append(line)

            # Process the last transaction on the page.
            if current_block:
                transaction = parse_transaction_block(
                    current_block,
                    page_number
                )

                if transaction:
                    transactions.append(transaction)

    return transactions


def parse_transaction_block(lines, page_number):

    block = "\n".join(lines)

    date_match = DATE_PATTERN.search(block)
    amount_match = AMOUNT_PATTERN.search(block)
    transaction_id_match = TRANSACTION_ID_PATTERN.search(block)
    utr_match = UTR_PATTERN.search(block)
    time_match = TIME_PATTERN.search(block)

    if not date_match or not amount_match:
        return None

    # Detect transaction direction.
    if re.search(r"\bCREDIT\b", block, re.IGNORECASE):
        transaction_type = "credit"

    elif re.search(r"\bDEBIT\b", block, re.IGNORECASE):
        transaction_type = "expense"

    else:
        return None

    # Extract date.
    transaction_date = datetime.strptime(
        date_match.group(1),
        "%b %d, %Y"
    ).date().isoformat()

    # Extract amount.
    amount = float(
        amount_match.group(1).replace(",", "")
    )

    # Extract merchant or counterparty.
    detail_match = re.search(
        r"(?:Paid to|Received from)\s+(.+?)"
        r"(?=\s+(?:CREDIT|DEBIT)\b|$)",
        block,
        re.IGNORECASE | re.DOTALL
    )

    counterparty = None

    if detail_match:
        counterparty = detail_match.group(1)
        counterparty = re.sub(r"\s+", " ", counterparty).strip()
        counterparty = re.sub(r"\s*❤$", "", counterparty).strip()

    # Extract time.
    transaction_time = None

    if time_match:
        transaction_time = datetime.strptime(
            time_match.group(1).upper(),
            "%I:%M %p"
        ).strftime("%H:%M:%S")

    return {
        "transaction_date": transaction_date,
        "transaction_time": transaction_time,
        "merchant": counterparty or "Unknown",
        "amount": amount,
        "transaction_type": transaction_type,
        "transaction_id": (
            transaction_id_match.group(1)
            if transaction_id_match else None
        ),
        "utr": utr_match.group(1) if utr_match else None,
        "source": "phonepe_statement",
        "page_number": page_number
    }