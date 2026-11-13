
from src.recurring_payment_detector import (
    annotate_recurring_payment_candidates
)


def make_transaction(day, category="Other"):
    return {
        "transaction_date": day,
        "merchant": "Google",
        "amount": "59.00",
        "transaction_type": "expense",
        "main_category": category,
        "category": category,
        "subcategory": "Uncategorised",
        "needs_review": True,
        "is_p2p": False,
        "is_internal_transfer": False
    }


def test_monthly_google_payment():

    transactions = [
        make_transaction("2026-08-01"),
        make_transaction("2026-09-01"),
        make_transaction("2026-10-01")
    ]

    annotate_recurring_payment_candidates(transactions)

    for tx in transactions:
        # Recurrence is a payment pattern, not proof of a subscription.
        # Keep the original category and attach recurrence metadata only.
        assert tx["main_category"] == "Other"
        assert tx["subcategory"] == "Uncategorised"
        assert tx["is_recurring_candidate"] is True
        assert tx["recurring_frequency"] == "monthly"


def test_two_payments_not_enough():

    transactions = [
        make_transaction("2026-09-01"),
        make_transaction("2026-10-01")
    ]

    annotate_recurring_payment_candidates(transactions)

    assert all(
        not tx.get("is_recurring_candidate", False)
        for tx in transactions
    )


def test_known_category_not_overwritten():

    transactions = [
        make_transaction("2026-08-01", "Entertainment"),
        make_transaction("2026-09-01", "Entertainment"),
        make_transaction("2026-10-01", "Entertainment")
    ]

    annotate_recurring_payment_candidates(transactions)

    assert all(
        tx["main_category"] == "Entertainment"
        for tx in transactions
    )
