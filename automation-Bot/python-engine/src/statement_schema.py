"""Canonical transaction schema shared by statement parsers."""
from decimal import Decimal, InvalidOperation

REQUIRED_FIELDS = ("transaction_date", "merchant", "transaction_description", "amount", "transaction_type")


def normalize_statement_transaction(transaction):
    """Return a canonical transaction dict while preserving parser-specific metadata."""
    if not isinstance(transaction, dict):
        raise TypeError("Each transaction must be a dictionary.")

    normalized = dict(transaction)
    for field in REQUIRED_FIELDS:
        value = normalized.get(field)
        if value is None or (isinstance(value, str) and not value.strip()):
            raise ValueError(f"Transaction is missing required field: {field}")

    try:
        amount = normalized["amount"]
        amount = amount if isinstance(amount, Decimal) else Decimal(str(amount))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError("Transaction amount must be a valid decimal number.") from exc

    if not amount.is_finite() or amount < 0:
        raise ValueError("Transaction amount must be finite and non-negative.")

    direction = str(normalized["transaction_type"]).strip().lower()
    if direction not in {"expense", "credit", "transfer"}:
        raise ValueError(f"Unsupported transaction_type: {direction!r}")

    normalized["transaction_date"] = str(normalized["transaction_date"]).strip()
    normalized["transaction_time"] = normalized.get("transaction_time") or None
    normalized["merchant"] = str(normalized["merchant"]).strip()
    normalized["transaction_description"] = str(normalized["transaction_description"]).strip()
    normalized["amount"] = amount
    normalized["transaction_type"] = direction
    normalized.setdefault("transaction_subtype", None)
    normalized.setdefault("payment_source", None)
    normalized.setdefault("credited_to", None)
    normalized.setdefault("transaction_id", None)
    normalized.setdefault("utr", None)
    normalized.setdefault("source", "unknown")
    return normalized


def normalize_statement_transactions(transactions):
    """Normalize a sequence of parser outputs into the canonical schema."""
    return [normalize_statement_transaction(item) for item in transactions]
