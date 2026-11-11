
from src.ride_payment_reconciliation import (
    detect_ride_event,
    confirm_ride_payment,
    match_ride_to_bank_transaction
)


def test_rapido_ride_detection():
    result = detect_ride_event(
        notification_title="Rapido",
        notification_text="Your ride is completed. Fare Rs 74."
    )

    assert result["provider"] == "Rapido"
    assert result["main_category"] == "Transport"
    assert result["ride_status"] == "completed"


def test_uber_ride_detection():
    result = detect_ride_event(
        notification_title="Uber",
        notification_text="Your trip is completed. Fare Rs 150."
    )

    assert result["provider"] == "Uber"
    assert result["main_category"] == "Transport"


def test_ride_does_not_assume_payment():
    result = detect_ride_event(
        notification_title="Rapido",
        notification_text="Ride completed. Fare Rs 74."
    )

    assert result["payment_status"] == "unconfirmed"
    assert result["payment_method"] is None
    assert result["needs_user_confirmation"] is True


def test_cash_payment_requires_confirmation():
    ride = detect_ride_event(
        notification_title="Rapido",
        notification_text="Ride completed. Fare Rs 74."
    )

    result = confirm_ride_payment(
        ride,
        payment_method="cash"
    )

    assert result["payment_method"] == "cash"
    assert result["payment_status"] == "paid"
    assert result["create_expense"] is True


def test_upi_payment_confirmation():
    ride = detect_ride_event(
        notification_title="Uber",
        notification_text="Trip completed. Fare Rs 150."
    )

    result = confirm_ride_payment(
        ride,
        payment_method="upi"
    )

    assert result["payment_method"] == "upi"
    assert result["create_expense"] is True


def test_bank_transaction_matching():
    ride = {
        "amount": 74,
        "event_time": "2026-11-11T17:00:00"
    }

    bank_transaction = {
        "amount": 74,
        "timestamp": "2026-11-11T17:05:00"
    }

    result = match_ride_to_bank_transaction(
        ride,
        bank_transaction
    )

    assert result["matched"] is True
    assert result["needs_review"] is True
