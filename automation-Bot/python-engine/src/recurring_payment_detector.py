"""Conservative recurring-payment pattern detection.

A recurring pattern is not proof of a subscription. This module only annotates
transactions with recurrence metadata and never changes their categories.
"""
from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from statistics import median
from src.merchant_normalizer import normalize_text

FREQUENCY_RANGES = {
    "weekly": (5, 9),
    "biweekly": (12, 16),
    "monthly": (24, 40),
    "quarterly": (80, 100),
    "yearly": (350, 380),
}


def _parse_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value or "").strip()
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%d %b %Y", "%d %B %Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    return None


def _amount(value):
    try:
        result = Decimal(str(value)).quantize(Decimal("0.01"))
        return result if result.is_finite() and result > 0 else None
    except (InvalidOperation, TypeError, ValueError):
        return None


def _frequency(intervals):
    if not intervals:
        return None
    typical = median(intervals)
    for name, (low, high) in FREQUENCY_RANGES.items():
        if low <= typical <= high and sum(low <= gap <= high for gap in intervals) >= max(1, len(intervals)-1):
            return name
    return None


def detect_recurring_payment_candidates(transactions, min_occurrences=3):
    """Find repeat expenses grouped by merchant and normalized service description.

    Amounts may vary modestly (e.g. tax/price changes); recurrence is determined
    primarily by merchant/service and cadence, not exact amount equality.
    """
    groups = defaultdict(list)
    for index, tx in enumerate(transactions):
        if str(tx.get("transaction_type", "")).lower() != "expense":
            continue
        if tx.get("is_p2p") or tx.get("is_internal_transfer") or tx.get("exclude_from_expense_total"):
            continue
        merchant = normalize_text(tx.get("merchant") or "")
        tx_date = _parse_date(tx.get("transaction_date"))
        amount = _amount(tx.get("amount"))
        if not merchant or tx_date is None or amount is None:
            continue
        # Keep the grouping merchant-led; descriptions often include changing IDs.
        groups[merchant].append({"date": tx_date, "index": index, "amount": amount})

    candidates = []
    for merchant, entries in groups.items():
        entries.sort(key=lambda x: (x["date"], x["index"]))
        # Same-day duplicate rows should not create a cadence.
        unique = []
        for entry in entries:
            if unique and entry["date"] == unique[-1]["date"]:
                continue
            unique.append(entry)
        if len(unique) < min_occurrences:
            continue
        intervals = [(unique[i]["date"] - unique[i-1]["date"]).days for i in range(1, len(unique))]
        frequency = _frequency(intervals)
        if not frequency:
            continue
        amounts = [x["amount"] for x in unique]
        latest = unique[-1]
        typical_gap = int(round(median(intervals)))
        avg = (sum(amounts) / len(amounts)).quantize(Decimal("0.01"))
        candidates.append({
            "merchant": merchant,
            "frequency": frequency,
            "occurrences": len(unique),
            "transaction_indices": [x["index"] for x in unique],
            "first_payment_date": unique[0]["date"].isoformat(),
            "last_payment_date": latest["date"].isoformat(),
            "next_expected_date": (latest["date"] + timedelta(days=typical_gap)).isoformat(),
            "interval_days": intervals,
            "amounts": [str(x) for x in amounts],
            "latest_amount": str(amounts[-1]),
            "average_amount": str(avg),
            "amount_changed": len(set(amounts)) > 1,
            "confidence": round(min(0.96, 0.68 + (len(unique)-3)*0.05), 2),
        })
    return candidates


def annotate_recurring_payment_candidates(transactions):
    """Add recurrence fields only; never overwrite category or P2P decisions."""
    candidates = detect_recurring_payment_candidates(transactions)
    for candidate in candidates:
        for index in candidate["transaction_indices"]:
            transactions[index].update({
                "is_recurring_candidate": True,
                "recurring_frequency": candidate["frequency"],
                "recurring_occurrences": candidate["occurrences"],
                "recurring_first_payment_date": candidate["first_payment_date"],
                "recurring_last_payment_date": candidate["last_payment_date"],
                "recurring_next_expected_date": candidate["next_expected_date"],
                "recurring_latest_amount": candidate["latest_amount"],
                "recurring_average_amount": candidate["average_amount"],
                "recurring_amount_changed": candidate["amount_changed"],
                "recurring_confidence": candidate["confidence"],
            })
    return transactions
