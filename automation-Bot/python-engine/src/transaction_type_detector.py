import re

PATTERNS = {
    "cashback": [
        r"\bcash\s*back\b", r"\bcashback\b",
        r"\breward\s*(?:credited|received)\b"
    ],
    "refund": [r"\brefund(?:ed)?\b", r"\breversal\b"],
    "wallet_topup": [
        r"\btop[\s-]?up(?:\s+(?:the\s+)?wallet)?\b",
        r"\bwallet\s+top[\s-]?up\b",
        r"\bwallet\s+load\b",
        r"\badded\s+to\s+(?:the\s+)?wallet\b",
        r"\bload(?:ed)?\s+(?:the\s+)?wallet\b"
    ],
    "subscription": [
        r"\bsubscription\b", r"\bmonthly\s+plan\b",
        r"\bauto[\s-]?pay\b", r"\brecurring\b"
    ],
}

def detect_transaction_type(description="", direction=None):
    """Detect cash-flow direction and special transaction subtype.

    direction accepts PhonePe/parser values: credit, expense, debit, income.
    The detector does not decide whether an unknown recipient is a person.
    """
    text = str(description or "").lower()
    direction_value = str(direction or "").lower().strip()

    subtype = next(
        (
            name for name, patterns in PATTERNS.items()
            if any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)
        ),
        None
    )

    txn_type = (
        "credit" if direction_value in {"credit", "income", "cr"}
        else "expense" if direction_value in {"debit", "expense", "dr"}
        else "unknown"
    )

    # Wallet funding moves money between the bank and wallet.
    if subtype == "wallet_topup" and txn_type == "expense":
        return {
            "transaction_type": "transfer",
            "transaction_subtype": "wallet_topup"
        }

    # Cashback/refunds are credits, but not salary/earned income.
    if subtype in {"cashback", "refund"} and txn_type == "credit":
        return {
            "transaction_type": "credit",
            "transaction_subtype": subtype
        }

    if subtype == "subscription" and txn_type == "expense":
        return {
            "transaction_type": "expense",
            "transaction_subtype": "subscription"
        }

    return {
        "transaction_type": txn_type,
        "transaction_subtype": subtype or "unknown"
    }
