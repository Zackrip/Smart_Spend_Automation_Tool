from unittest import result

import pytest

from src.notification_parser import extract_transaction
from src.transaction_classifier import classify_transaction


# ==========================================
# PARSER TESTS
# ==========================================

def test_upi_payment():
    result = extract_transaction(
        "Paid Rs. 450 to Rahul Sharma using UPI."
    )

    assert result["amount"] == 450
    assert result["transaction_type"] == "expense"
    assert result["counterparty"] is not None
    assert result["payment_method"] == "UPI"


def test_bank_debit():
    result = extract_transaction(
        "Your account is debited by INR 750."
    )

    assert result["amount"] == 750
    assert result["transaction_type"] == "expense"


def test_bank_credit():
    result = extract_transaction(
        "Rs. 5000 credited to your account."
    )

    assert result["amount"] == 5000
    assert result["transaction_type"] == "income"


def test_refund():
    result = extract_transaction(
        "Refund of Rs. 499 processed."
    )

    assert result["amount"] == 499
    assert result["transaction_type"] == "refund"


def test_failed_payment():
    result = extract_transaction(
        "Your payment of Rs. 350 has failed."
    )

    assert result["amount"] == 350
    assert result["transaction_type"] == "failed"


def test_atm_withdrawal():
    result = extract_transaction(
        "ATM withdrawal of Rs. 2000 successful."
    )

    assert result["amount"] == 2000
    assert result["transaction_type"] == "expense"
    assert result["payment_method"] == "ATM"


def test_counterparty_missing():
    result = extract_transaction(
        "Your account is debited by Rs. 750."
    )

    assert result["amount"] == 750
    assert result["counterparty"] is None


def test_empty_notification():
    with pytest.raises(ValueError):
        extract_transaction("")


# ==========================================
# CLASSIFIER TESTS
# ==========================================

def test_swiggy_food():
    result = classify_transaction(
        counterparty="Swiggy"
    )

    assert result["category"] == "Food"


def test_blinkit_groceries():
    result = classify_transaction(
        counterparty="Blinkit"
    )

    assert result["category"] == "Groceries"


def test_uber_travel():
    result = classify_transaction(
        counterparty="Uber"
    )

    assert result["category"] == "Transport"
    assert result["subcategory"] == "Cab"


def test_dhaba_food():
    result = classify_transaction(
        counterparty="Sharma Dhaba"
    )

    assert result["category"] == "Food"


def test_unknown_person_needs_review():
    result = classify_transaction(
        counterparty="Mohit Kumar"
    )

    assert result["category"] == "Other"
    assert result["needs_review"] is True


def test_user_confirmed_category():
    result = classify_transaction(
        counterparty="Mohit Kumar",
        user_category="Food"
    )

    assert result["category"] == "Food"
    assert result["classification_method"] == "user_confirmed"
