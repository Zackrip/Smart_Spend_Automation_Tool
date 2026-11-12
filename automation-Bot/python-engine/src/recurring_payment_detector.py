
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from src.merchant_normalizer import normalize_text


def _parse_date(value):
    if isinstance(value, date):
        return value

    text = str(value or "").strip()

    for fmt in (
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%d %b %Y"
    ):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue

    return None


def _amount_key(value):
    try:
        return Decimal(str(value)).quantize(
            Decimal("0.01")
        )
    except (InvalidOperation, TypeError, ValueError):
        return None


def detect_recurring_payment_candidates(
    transactions,
    min_occurrences=3,
    min_interval_days=24,
    max_interval_days=40
):
    """
    Detect repeated payments with:
    - Same merchant
    - Same amount
    - At least 3 occurrences
    - Monthly intervals of 24–40 days
    """

    groups = defaultdict(list)

    for index, tx in enumerate(transactions):

        if tx.get("transaction_type") != "expense":
            continue

        merchant = normalize_text(
            tx.get("merchant") or ""
        )

        amount = _amount_key(tx.get("amount"))

        tx_date = _parse_date(
            tx.get("transaction_date")
        )

        if not merchant or amount is None or tx_date is None:
            continue

        groups[(merchant, amount)].append(
            (tx_date, index)
        )

    candidates = []

    for (merchant, amount), entries in groups.items():

        entries.sort(key=lambda item: item[0])

        runs = []
        current = []

        for entry in entries:

            if not current:
                current = [entry]
                continue

            gap = (
                entry[0] - current[-1][0]
            ).days

            if min_interval_days <= gap <= max_interval_days:
                current.append(entry)
            else:
                runs.append(current)
                current = [entry]

        if current:
            runs.append(current)

        best = max(runs, key=len, default=[])

        if len(best) >= min_occurrences:

            candidates.append({
                "merchant": merchant,
                "amount": str(amount),
                "occurrences": len(best),
                "transaction_indices": [
                    index for _, index in best
                ],
                "interval_days": [
                    (
                        best[i][0] - best[i - 1][0]
                    ).days
                    for i in range(1, len(best))
                ]
            })

    return candidates


def annotate_recurring_payment_candidates(transactions):

    candidates = detect_recurring_payment_candidates(
        transactions
    )

    for candidate in candidates:

        for index in candidate["transaction_indices"]:

            tx = transactions[index]

            # Never overwrite known merchant categories.
            if tx.get("main_category") not in {
                None, "Other"
            }:
                continue

            if tx.get("is_p2p") or tx.get("is_internal_transfer"):
                continue

            tx.update({
                "category": "Subscriptions",
                "main_category": "Subscriptions",
                "subcategory": "Other Subscription",

                "classification_method":
                    "recurring_payment_candidate",

                "confidence": 0.75,

                # User must confirm the subscription.
                "needs_review": True,

                "is_recurring_candidate": True,
                "recurring_interval": "monthly",
                "recurring_occurrences":
                    candidate["occurrences"],

                "recurring_amount": candidate["amount"]
            })

    return transactions
