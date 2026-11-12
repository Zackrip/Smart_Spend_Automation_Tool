"""Parser for PhonePe transaction-statement CSV exports.

The parser is intentionally separate from the existing PDF parser. It returns
transactions in the same core shape used by src/statement_parser.py so the
existing classification pipeline can be reused in a later integration phase.
"""

import csv
import io
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Optional, Tuple


REQUIRED_COLUMNS = {
    "date",
    "time",
    "transaction details",
    "transaction id",
    "utr",
    "transaction type",
    "credit/debit instrument",
    "amount",
}


def _clean(value: Optional[str]) -> str:
    return re.sub(r"\s+", " ", (value or "")).strip().rstrip("♥❤").strip()


def _decode_csv(csv_bytes: bytes) -> str:
    """Decode common PhonePe CSV encodings without changing source data."""
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return csv_bytes.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("Could not decode the uploaded CSV file.")


def _find_header_row(lines: List[str]) -> int:
    """Find the actual CSV header, even when statement metadata precedes it."""
    for index, line in enumerate(lines):
        try:
            cells = next(csv.reader([line]))
        except (csv.Error, StopIteration):
            continue
        normalized = {cell.strip().lower() for cell in cells}
        if REQUIRED_COLUMNS.issubset(normalized):
            return index
    raise ValueError(
        "PhonePe CSV header was not found. Expected columns: "
        + ", ".join(sorted(REQUIRED_COLUMNS))
    )


def _parse_date(value: str) -> str:
    value = _clean(value)
    # PhonePe sometimes writes September as "Sept" instead of "Sep".
    value = re.sub(r"^Sept\b", "Sep", value, flags=re.IGNORECASE)
    for date_format in ("%b %d, %Y", "%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, date_format).date().isoformat()
        except ValueError:
            pass
    raise ValueError(f"Invalid transaction date: {value!r}")


def _parse_time(value: str) -> Optional[str]:
    value = _clean(value)
    if not value:
        return None
    for time_format in ("%I:%M %p", "%I:%M:%S %p", "%H:%M", "%H:%M:%S"):
        try:
            return datetime.strptime(value.upper(), time_format).strftime("%H:%M:%S")
        except ValueError:
            pass
    return None


def _parse_amount(value: str) -> Decimal:
    cleaned = _clean(value).replace(",", "").replace("₹", "").strip()
    try:
        amount = Decimal(cleaned)
    except (InvalidOperation, ValueError):
        raise ValueError(f"Invalid transaction amount: {value!r}")
    if not amount.is_finite() or amount < 0:
        raise ValueError(f"Transaction amount must be a finite non-negative number: {value!r}")
    return amount


def _counterparty_and_subtype(description: str) -> Tuple[str, Optional[str]]:
    """Extract a counterparty label; this does not decide person vs merchant."""
    description = _clean(description)
    patterns = (
        (r"^(?:Paid to|Payment to)\s+(.+)$", None),
        (r"^Received from\s+(.+)$", "personal_or_external_credit"),
        (r"^Cashback from\s+(.+)$", "cashback"),
        (r"^(?:Refund from|Refund for)\s+(.+)$", "refund"),
        (r"^(?:Reversal from|Payment reversal)\s+(.+)$", "refund"),
    )
    for pattern, subtype in patterns:
        match = re.match(pattern, description, flags=re.IGNORECASE)
        if match:
            return _clean(match.group(1)), subtype

    bill_patterns = (
        (r"^Electricity bill paid\b", "Electricity Bill"),
        (r"^Insurance Success\b", "Insurance"),
        (r"^Mobile bill paid\b", "Mobile Bill"),
        (r"^Mobile recharged\b", "Mobile Recharge"),
        (r"^Credit card bill paid\b", "Credit Card Bill"),
        (r"^Broadband bill paid\b", "Broadband Bill"),
        (r"^DTH recharge\b", "DTH Recharge"),
    )
    for pattern, label in bill_patterns:
        if re.search(pattern, description, flags=re.IGNORECASE):
            return label, "bill_payment"

    if re.search(r"^(?:Top[- ]?up\s+Wallet|Wallet\s+Top[- ]?up|Added to Wallet)$", description, re.I):
        return "Wallet", "wallet_top_up"

    return description or "Unknown", "unclassified_description"


def _normalise_row(row: Dict[str, str], row_number: int) -> Dict:
    """Convert one CSV row into the shared transaction dictionary shape."""
    # DictReader keys are normalised before this function is called.
    description = _clean(row.get("transaction details"))
    direction = _clean(row.get("transaction type")).upper()
    if direction not in {"DEBIT", "CREDIT"}:
        raise ValueError(f"Unsupported transaction type: {direction!r}")
    if not description:
        raise ValueError("Missing transaction details")

    transaction_date = _parse_date(row.get("date", ""))
    amount = _parse_amount(row.get("amount", ""))
    merchant, subtype = _counterparty_and_subtype(description)

    instrument = _clean(row.get("credit/debit instrument"))
    payment_source = None
    credited_to = None
    if instrument.lower().startswith("paid by"):
        payment_source = _clean(re.sub(r"^paid by\s*", "", instrument, flags=re.I)) or None
    elif instrument.lower().startswith("credited to"):
        credited_to = _clean(re.sub(r"^credited to\s*", "", instrument, flags=re.I)) or None

    return {
        "transaction_date": transaction_date,
        "transaction_time": _parse_time(row.get("time", "")),
        "merchant": merchant,
        "transaction_description": description,
        "transaction_subtype": subtype,
        "amount": amount,
        "transaction_type": "credit" if direction == "CREDIT" else "expense",
        "payment_source": payment_source,
        "credited_to": credited_to,
        "transaction_id": _clean(row.get("transaction id")) or None,
        "utr": _clean(row.get("utr")) or None,
        "source": "phonepe_csv",
        "source_row_number": row_number,
        "original_transaction_type": direction,
        "credit_debit_instrument": instrument or None,
    }


def extract_phonepe_csv_transactions(csv_bytes: bytes) -> List[Dict]:
    """Extract valid PhonePe CSV transactions as normalized dictionaries.

    Metadata/disclaimer lines are ignored. Rows that are not transaction rows
    (for example, footer text) are skipped. A malformed row that looks like a
    transaction raises ValueError with its CSV row number, rather than being
    silently discarded.
    """
    if not isinstance(csv_bytes, (bytes, bytearray)):
        raise TypeError("csv_bytes must be bytes or bytearray")
    if not csv_bytes:
        raise ValueError("The uploaded CSV file is empty.")

    text = _decode_csv(bytes(csv_bytes))
    lines = text.splitlines()
    header_index = _find_header_row(lines)
    reader = csv.DictReader(io.StringIO("\n".join(lines[header_index:])))
    if not reader.fieldnames:
        raise ValueError("CSV header is missing or invalid.")

    # Normalise header names while preserving row values.
    reader.fieldnames = [name.strip().lower() for name in reader.fieldnames]
    transactions = []
    for row in reader:
        if not row:
            continue
        normalized = {
            (key or "").strip().lower(): (value or "").strip()
            for key, value in row.items()
            if key is not None
        }
        # Footer/disclaimer lines do not have a valid date and direction.
        date_value = normalized.get("date", "")
        direction = normalized.get("transaction type", "").upper()
        if direction not in {"DEBIT", "CREDIT"}:
            continue
        if not date_value:
            continue
        csv_row_number = header_index + reader.line_num + 1
        try:
            transactions.append(_normalise_row(normalized, csv_row_number))
        except ValueError as exc:
            raise ValueError(f"Invalid PhonePe transaction at CSV row {csv_row_number}: {exc}") from exc

    if not transactions:
        raise ValueError("No valid PhonePe transactions were found in the CSV file.")
    return transactions
