"""Helpers for PhonePe statement API responses."""

from collections import defaultdict
from decimal import Decimal


def _as_float(value):
    if isinstance(value, Decimal):
        return float(value)
    return float(value or 0)


def build_statement_overview(result):
    """Build a JSON-safe overview while retaining classified transactions."""
    transactions = result.get("transactions", [])
    category_totals = defaultdict(float)
    for tx in transactions:
        if (
            tx.get("transaction_type") == "expense"
            and not tx.get("exclude_from_expense_total", False)
        ):
            category = tx.get("category") or "Other"
            category_totals[str(category)] += _as_float(tx.get("amount"))

    safe_transactions = []
    for tx in transactions:
        safe = dict(tx)
        safe["amount"] = _as_float(safe.get("amount"))
        # Convert Decimal/date-like values to JSON-safe strings.
        for key, value in list(safe.items()):
            if isinstance(value, Decimal):
                safe[key] = float(value)
            elif hasattr(value, "isoformat"):
                safe[key] = value.isoformat()
        safe_transactions.append(safe)

    return {
        "summary": {
            "total_transactions": int(result.get("total_transactions", len(transactions))),
            "total_expenses": _as_float(result.get("total_expenses")),
            "total_credits": _as_float(result.get("total_credits")),
            "total_income": _as_float(result.get("total_income")),
            "total_internal_transfers": _as_float(result.get("total_internal_transfers")),
            "transactions_needing_review": int(result.get("transactions_needing_review", 0)),
            "unclassified_transactions": int(result.get("unclassified_transactions", 0)),
            "awaiting_user_confirmation": int(result.get("awaiting_user_confirmation", 0)),
            "autopay_transactions": sum(1 for tx in transactions if tx.get("payment_mode") == "autopay"),
            "payment_mode_unknown": sum(1 for tx in transactions if tx.get("payment_mode", "unknown") == "unknown"),
        },
        "category_wise_expenses": [
            {"category": category, "amount": round(amount, 2)}
            for category, amount in sorted(
                category_totals.items(), key=lambda item: item[1], reverse=True
            )
        ],
        "transactions": safe_transactions,
    }
