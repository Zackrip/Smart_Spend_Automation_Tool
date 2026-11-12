"""PhonePe-specific rules for wallet, cashback and refunds."""
import re

def _text(*values):
    return " ".join(str(v) for v in values if v).lower()

def detect_phonepe_special_case(transaction):
    description = _text(
        transaction.get("transaction_description"),
        transaction.get("description"),
        transaction.get("merchant"),
        transaction.get("payment_source"),
        transaction.get("credited_to")
    )
    direction = str(transaction.get("transaction_type") or "").lower()

    # Be deliberately specific: a normal purchase paid using a wallet is NOT
    # a wallet top-up. Only explicit wallet-loading language is a top-up.
    wallet_topup = bool(re.search(
        r"\b(?:top[\s-]?up(?:\s+(?:the\s+)?wallet)?|wallet\s+top[\s-]?up|"
        r"wallet\s+load|added\s+to\s+(?:the\s+)?wallet|"
        r"load(?:ed)?\s+(?:the\s+)?wallet)\b",
        description
    ))
    cashback = bool(re.search(r"\bcash\s*back\b|\bcashback\b", description))
    refund = bool(re.search(r"\brefund(?:ed)?\b|\breversal\b", description))

    if wallet_topup and direction in {"expense", "debit"}:
        return {
            "special_type": "wallet_topup",
            "category": "Internal Transfers",
            "main_category": "Internal Transfers",
            "subcategory": "Wallet Top-up",
            "transaction_type": "transfer",
            "transaction_subtype": "wallet_topup",
            "classification_method": "phonepe_wallet_topup_rule",
            "confidence": 0.99,
            "needs_review": False,
            "exclude_from_expense_total": True,
            "exclude_from_income_total": True,
            "is_internal_transfer": True
        }

    if cashback and direction in {"credit", "income"}:
        return {
            "special_type": "cashback",
            "category": "Cashback & Rewards",
            "main_category": "Cashback & Rewards",
            "subcategory": "PhonePe Cashback",
            "transaction_type": "credit",
            "transaction_subtype": "cashback",
            "classification_method": "phonepe_cashback_rule",
            "confidence": 0.99,
            "needs_review": False,
            "exclude_from_expense_total": True,
            "exclude_from_income_total": True,
            "is_internal_transfer": False
        }

    if refund and direction in {"credit", "income"}:
        return {
            "special_type": "refund",
            "category": "Refunds",
            "main_category": "Refunds",
            "subcategory": "Purchase Refund",
            "transaction_type": "credit",
            "transaction_subtype": "refund",
            "classification_method": "refund_rule",
            "confidence": 0.97,
            "needs_review": False,
            "exclude_from_expense_total": True,
            "exclude_from_income_total": True,
            "is_internal_transfer": False
        }

    return None

def detect_payment_source(transaction):
    """Payment source is metadata; it does not change the purchase category."""
    values = _text(
        transaction.get("payment_source"),
        transaction.get("transaction_description"),
        transaction.get("description")
    )
    if "wallet" in values:
        return "Wallet"
    if "gift card" in values:
        return "Gift Card"
    if "bank" in values or "account" in values:
        return "Bank"
    return transaction.get("payment_source") or "Unknown"
