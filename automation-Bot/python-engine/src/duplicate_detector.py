"""Conservative duplicate transaction detection.

Only exact provider identifiers or exact same date/time/merchant/amount/direction
fingerprints are flagged. Similar same-day purchases are not enough.
"""
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from src.merchant_normalizer import normalize_text


def _amount(value):
    try:
        return str(Decimal(str(value)).quantize(Decimal("0.01")))
    except (InvalidOperation, TypeError, ValueError):
        return None


def detect_duplicate_transactions(transactions):
    groups = defaultdict(list)
    for index, tx in enumerate(transactions):
        txid = str(tx.get("transaction_id") or "").strip()
        utr = str(tx.get("utr") or "").strip()
        if txid:
            groups[("transaction_id", txid)].append(index)
        elif utr:
            groups[("utr", utr)].append(index)
        else:
            key = (
                "fingerprint",
                str(tx.get("transaction_date") or ""),
                str(tx.get("transaction_time") or ""),
                normalize_text(tx.get("merchant") or ""),
                _amount(tx.get("amount")),
                str(tx.get("transaction_type") or "").lower(),
            )
            # Do not use a weak fingerprint without time and merchant.
            if key[2] and key[3] and key[4]:
                groups[key].append(index)
    duplicates = []
    for key, indices in groups.items():
        if len(indices) < 2:
            continue
        first = indices[0]
        for duplicate_index in indices[1:]:
            tx = transactions[duplicate_index]
            tx.update({
                "is_duplicate_candidate": True,
                "duplicate_of_index": first,
                "duplicate_match_method": key[0],
                "duplicate_group_size": len(indices),
                "needs_review": True,
            })
            duplicates.append({
                "transaction_index": duplicate_index,
                "original_transaction_index": first,
                "match_method": key[0],
                "group_size": len(indices),
            })
    return duplicates


def annotate_duplicate_transactions(transactions):
    detect_duplicate_transactions(transactions)
    return transactions
