import re

PATTERNS = {
    "cashback": [r"\bcash\s*back\b", r"\bcashback\b"],
    "refund": [r"\brefund(?:ed)?\b", r"\breversal\b"],
    "wallet_topup": [r"\btop[\s-]?up\b", r"\bwallet\s+load\b", r"\badded\s+to\s+wallet\b"],
    "subscription": [r"\bsubscription\b", r"\bmonthly\s+plan\b", r"\bauto[\s-]?pay\b", r"\brecurring\b"],
}

def detect_transaction_type(description="", direction=None):
    text = (description or "").lower()
    subtype = None
    for candidate, patterns in PATTERNS.items():
        if any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns):
            subtype = candidate
            break

    direction_value = (direction or "").lower()
    txn_type = "credit" if direction_value in {"credit", "income"} else (
        "expense" if direction_value in {"debit", "expense"} else "unknown"
    )

    if subtype in {"cashback", "refund"} and txn_type == "credit":
        return {"transaction_type": "credit", "transaction_subtype": subtype}
    if subtype == "wallet_topup" and txn_type == "expense":
        return {"transaction_type": "transfer", "transaction_subtype": subtype}
    if subtype == "subscription" and txn_type == "expense":
        return {"transaction_type": "expense", "transaction_subtype": subtype}
    return {"transaction_type": txn_type, "transaction_subtype": subtype or "unknown"}
