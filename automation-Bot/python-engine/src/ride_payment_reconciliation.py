"""Ride/service detection and payment reconciliation primitives for Paisora.

Ride completion is not proof of payment. This module never creates a paid
expense from a completed ride until the user confirms the payment method/status.
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import Optional

PROVIDERS = {
    "rapido": ["rapido", "rapido bike taxi", "rapido parcel"],
    "uber": ["uber", "uber go", "uber auto", "uber moto", "uber cab"],
    "ola": ["ola", "ola cabs", "ola auto", "ola bike"]
}

SERVICE_RULES = [
    (["parcel", "delivery"], "Parcel Delivery"),
    (["bike taxi", "bike ride", "moto", "captain"], "Bike Taxi"),
    (["auto", "three wheeler"], "Auto"),
    (["cab", "taxi", "car ride", "uber go"], "Cab")
]

def _norm(value):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", (value or "").lower())).strip()

def detect_ride_event(notification_title=None, notification_text=None,
                       package_name=None, email_sender=None,
                       amount: Optional[float]=None, event_time=None):
    """Detect provider/service from app package, title, body or email sender."""
    raw = " ".join(x for x in (package_name, notification_title, notification_text, email_sender) if isinstance(x, str))
    text = _norm(raw)
    provider = None

    # App package identity is strong evidence, but only if it contains a provider token.
    for name, aliases in PROVIDERS.items():
        if any(_norm(alias) in text for alias in aliases) or name in text:
            provider = name.title()
            break
    if not provider:
        return None

    service = None
    for cues, label in SERVICE_RULES:
        if any(_norm(cue) in text for cue in cues):
            service = label
            break
    if service is None:
        service = "Cab" if provider in {"Uber", "Ola"} else "Bike Taxi"

    amount_match = re.search(r"(?:₹|rs\.?|inr)\s*([0-9,]+(?:\.[0-9]{1,2})?)", notification_text or "", re.I)
    parsed_amount = amount
    if parsed_amount is None and amount_match:
        parsed_amount = float(amount_match.group(1).replace(",", ""))

    lower = text
    status = "completed" if any(x in lower for x in ["completed", "ride complete", "ride completed", "trip completed", "delivered"]) else (
        "cancelled" if "cancelled" in lower or "canceled" in lower else "unknown"
    )

    return {
        "provider": provider,
        "service": service,
        "main_category": "Transport",
        "category": "Transport",
        "subcategory": service,
        "amount": parsed_amount,
        "event_time": event_time,
        "ride_status": status,
        "payment_status": "unconfirmed",
        "payment_method": None,
        "needs_user_confirmation": status == "completed",
        "classification_method": "service_notification"
    }

def confirm_ride_payment(ride_event, payment_method, payment_status="paid"):
    """Apply an explicit user choice. No automatic cash inference is performed."""
    allowed_methods = {"cash", "upi", "wallet", "card", "other", "not_paid", "unknown"}
    if payment_method not in allowed_methods:
        raise ValueError(f"payment_method must be one of {sorted(allowed_methods)}")
    updated = dict(ride_event)
    updated["payment_method"] = payment_method
    if payment_method in {"not_paid", "unknown"}:
        updated["payment_status"] = "unconfirmed" if payment_method == "unknown" else "pending"
    else:
        updated["payment_status"] = payment_status
    updated["needs_user_confirmation"] = payment_method == "unknown"
    updated["create_expense"] = payment_method != "not_paid" and payment_method != "unknown" and payment_status == "paid"
    return updated

def match_ride_to_bank_transaction(ride_event, bank_transaction, time_window_minutes=30):
    """Conservative amount/time match. Returns candidate status; never inserts data."""
    ride_amount = ride_event.get("amount")
    bank_amount = bank_transaction.get("amount")
    if ride_amount is None or bank_amount is None:
        return {"matched": False, "reason": "missing_amount", "needs_review": True}
    if round(float(ride_amount), 2) != round(float(bank_amount), 2):
        return {"matched": False, "reason": "amount_mismatch", "needs_review": True}

    ride_time = ride_event.get("event_time")
    bank_time = bank_transaction.get("timestamp")
    if ride_time and bank_time:
        try:
            r = datetime.fromisoformat(ride_time) if isinstance(ride_time, str) else ride_time
            b = datetime.fromisoformat(bank_time) if isinstance(bank_time, str) else bank_time
            delta = abs((r - b).total_seconds()) / 60
            if delta > time_window_minutes:
                return {"matched": False, "reason": "outside_time_window", "needs_review": True}
        except (TypeError, ValueError):
            return {"matched": False, "reason": "invalid_timestamp", "needs_review": True}

    return {
        "matched": True,
        "match_type": "amount_time_candidate",
        "reason": "same_amount_within_time_window",
        "needs_review": True,
        "note": "Confirm provider/narration or user approval before linking; amount and time alone are not proof."
    }
