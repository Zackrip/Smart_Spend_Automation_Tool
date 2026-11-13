from src.recurring_payment_detector import detect_recurring_payment_candidates, annotate_recurring_payment_candidates
from src.duplicate_detector import detect_duplicate_transactions
from src.review_queue import build_transaction_review_queue
from src.merchant_intelligence import identify_merchant
from src.transaction_intelligence import enrich_transaction_intelligence


def tx(date, merchant="Netflix", amount=199, **extra):
    value = {
        "transaction_date": date, "transaction_time": "10:00:00",
        "merchant": merchant, "transaction_description": f"Payment to {merchant}",
        "amount": amount, "transaction_type": "expense", "confidence": 0.9,
        "needs_review": False,
    }
    value.update(extra)
    return value


def test_monthly_recurring_with_amount_change():
    rows = [tx("2026-01-10", amount=199), tx("2026-02-10", amount=199), tx("2026-03-10", amount=219)]
    found = detect_recurring_payment_candidates(rows)
    assert len(found) == 1
    assert found[0]["frequency"] == "monthly"
    assert found[0]["amount_changed"] is True
    assert found[0]["next_expected_date"] == "2026-04-09"


def test_recurring_annotation_does_not_rewrite_category():
    rows = [tx("2026-01-10"), tx("2026-02-10"), tx("2026-03-10")]
    for row in rows:
        row["main_category"] = "Entertainment"
        row["category"] = "Entertainment"
        row["subcategory"] = "OTT Subscription"
    annotate_recurring_payment_candidates(rows)
    assert all(row["main_category"] == "Entertainment" for row in rows)
    assert all(row["is_recurring_candidate"] for row in rows)


def test_weekly_recurring_detection():
    rows = [tx("2026-01-01"), tx("2026-01-08"), tx("2026-01-15")]
    assert detect_recurring_payment_candidates(rows)[0]["frequency"] == "weekly"


def test_p2p_and_internal_transfers_not_recurring():
    rows = [tx("2026-01-01", merchant="Rahul Sharma", is_p2p=True), tx("2026-02-01", merchant="Rahul Sharma", is_p2p=True), tx("2026-03-01", merchant="Rahul Sharma", is_p2p=True)]
    assert detect_recurring_payment_candidates(rows) == []


def test_exact_transaction_id_duplicate():
    rows = [tx("2026-01-01", transaction_id="abc"), tx("2026-01-01", transaction_id="abc")]
    duplicates = detect_duplicate_transactions(rows)
    assert len(duplicates) == 1
    assert rows[1]["is_duplicate_candidate"] is True
    assert rows[1]["needs_review"] is True


def test_same_day_same_merchant_different_time_not_duplicate():
    rows = [tx("2026-01-01", transaction_time="10:00:00"), tx("2026-01-01", transaction_time="18:00:00")]
    assert detect_duplicate_transactions(rows) == []


def test_review_queue_uses_confidence_and_flags():
    rows = [tx("2026-01-01", confidence=0.3), tx("2026-01-02", confidence=0.95, needs_review=False)]
    rows[1]["is_duplicate_candidate"] = True
    queue = build_transaction_review_queue(rows)
    assert [item["transaction_index"] for item in queue] == [0, 1]


def test_merchant_identity_metadata_without_category_mutation():
    result = identify_merchant("Netflix")
    assert result["merchant_normalized"] == "netflix"
    assert result["merchant_match_category"] == "Entertainment"


def test_end_to_end_intelligence_summary():
    rows = [tx("2026-01-10"), tx("2026-02-10"), tx("2026-03-10")]
    result = enrich_transaction_intelligence(rows)
    assert result["intelligence_summary"]["recurring_patterns_detected"] == 1
    assert result["transactions"][0]["is_recurring_candidate"] is True
