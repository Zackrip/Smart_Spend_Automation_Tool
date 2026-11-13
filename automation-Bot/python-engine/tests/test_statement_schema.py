from decimal import Decimal
import pytest

from src.statement_schema import normalize_statement_transaction, normalize_statement_transactions


def sample(**updates):
    item = {
        "transaction_date": "2026-11-10",
        "transaction_time": "22:44:00",
        "merchant": "Google",
        "transaction_description": "Payment to Google",
        "amount": Decimal("59.00"),
        "transaction_type": "expense",
        "source": "phonepe_csv",
    }
    item.update(updates)
    return item


def test_normalizes_csv_transaction_and_preserves_source_fields():
    result = normalize_statement_transaction(sample(original_transaction_type="DEBIT", utr="UTR1"))
    assert result["amount"] == Decimal("59.00")
    assert result["transaction_type"] == "expense"
    assert result["source"] == "phonepe_csv"
    assert result["original_transaction_type"] == "DEBIT"
    assert result["utr"] == "UTR1"
    assert result["credited_to"] is None


def test_normalizes_pdf_style_transaction_without_losing_metadata():
    result = normalize_statement_transaction(sample(source="phonepe_statement", page_number=2))
    assert result["source"] == "phonepe_statement"
    assert result["page_number"] == 2


def test_rejects_invalid_direction():
    with pytest.raises(ValueError, match="Unsupported transaction_type"):
        normalize_statement_transaction(sample(transaction_type="DEBIT"))


def test_rejects_negative_amount():
    with pytest.raises(ValueError, match="non-negative"):
        normalize_statement_transaction(sample(amount=Decimal("-1")))


def test_normalizes_list():
    result = normalize_statement_transactions([sample(), sample(merchant="Store")])
    assert len(result) == 2
    assert result[1]["merchant"] == "Store"


def test_schema_preserves_explicit_autopay_and_unknown():
    base = sample()
    autopay = normalize_statement_transaction({**base, "payment_mode": "autopay"})
    unknown = normalize_statement_transaction({**base, "payment_mode": "unknown"})
    assert autopay["is_autopay"] is True
    assert unknown["is_autopay"] is None
