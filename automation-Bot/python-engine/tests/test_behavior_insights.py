import pytest
from src.behavior_insights import generate_behavior_insights


@pytest.fixture
def sample():
    return [
        {"transaction_date":"2026-10-03","amount":80,"transaction_type":"expense","main_category":"Food","merchant":"Swiggy"},
        {"transaction_date":"2026-10-04","amount":90,"transaction_type":"expense","main_category":"Food","merchant":"Swiggy"},
        {"transaction_date":"2026-10-05","amount":500,"transaction_type":"expense","main_category":"Shopping","merchant":"Myntra"},
        {"transaction_date":"2026-10-06","amount":70,"transaction_type":"expense","main_category":"Food","merchant":"Swiggy"},
        {"transaction_date":"2026-10-07","amount":60,"transaction_type":"expense","main_category":"Food","merchant":"Swiggy"},
        {"transaction_date":"2026-10-08","amount":50,"transaction_type":"expense","main_category":"Food","merchant":"Swiggy"},
        {"transaction_date":"2026-10-10","amount":1200,"transaction_type":"expense","main_category":"Food","merchant":"Swiggy"},
        {"transaction_date":"2026-10-11","amount":1000,"transaction_type":"expense","main_category":"Food","merchant":"Swiggy"},
        {"transaction_date":"2026-10-12","amount":300,"transaction_type":"expense","main_category":"Transport","merchant":"Uber"},
    ]


def test_detects_frequent_small_transactions(sample):
    result = generate_behavior_insights(sample, as_of="2026-10-20")
    insight = next(x for x in result["insights"] if x["insight_type"] == "frequent_small_transactions")
    assert insight["transaction_count"] == 5
    assert insight["total_amount"] == 350


def test_detects_frequent_merchant(sample):
    result = generate_behavior_insights(sample, as_of="2026-10-20", frequent_merchant_min_count=5)
    insight = next(x for x in result["insights"] if x["insight_type"] == "frequent_merchant")
    assert insight["merchant"] == "Swiggy"
    assert insight["transaction_count"] == 7


def test_detects_merchant_concentration(sample):
    result = generate_behavior_insights(sample, as_of="2026-10-20")
    assert any(x["insight_type"] == "merchant_spending_concentration" for x in result["insights"])



def test_weekend_average_compared_with_weekday_average():
    rows = [
        {"transaction_date": "2026-10-05", "amount": 100, "transaction_type": "expense", "main_category": "Food"},
        {"transaction_date": "2026-10-06", "amount": 100, "transaction_type": "expense", "main_category": "Food"},
        {"transaction_date": "2026-10-07", "amount": 100, "transaction_type": "expense", "main_category": "Food"},
        {"transaction_date": "2026-10-08", "amount": 100, "transaction_type": "expense", "main_category": "Food"},
        {"transaction_date": "2026-10-10", "amount": 400, "transaction_type": "expense", "main_category": "Food"},
        {"transaction_date": "2026-10-11", "amount": 400, "transaction_type": "expense", "main_category": "Food"},
    ]

    result = generate_behavior_insights(
        rows,
        as_of="2026-10-20"
    )

    assert result["metrics"]["weekend_comparison_available"] is True

    assert any(
        x["insight_type"] == "weekend_spending_higher"
        for x in result["insights"]
    )
def test_weekend_comparison_skipped_with_insufficient_weekdays():
    rows = [
        {"transaction_date": "2026-10-05", "amount": 100, "transaction_type": "expense", "main_category": "Food"},
        {"transaction_date": "2026-10-06", "amount": 100, "transaction_type": "expense", "main_category": "Food"},
        {"transaction_date": "2026-10-10", "amount": 400, "transaction_type": "expense", "main_category": "Food"},
        {"transaction_date": "2026-10-11", "amount": 400, "transaction_type": "expense", "main_category": "Food"},
    ]

    result = generate_behavior_insights(
        rows,
        as_of="2026-10-20"
    )

    assert result["metrics"]["weekend_comparison_available"] is False

    assert not any(
        x["insight_type"] == "weekend_spending_higher"
        for x in result["insights"]
    )

def test_ignores_credits_and_personal_transfers():
    rows = [
        {"transaction_date":"2026-10-03","amount":100,"transaction_type":"expense","main_category":"Personal Transfers","merchant":"Friend"},
        {"transaction_date":"2026-10-04","amount":500,"transaction_type":"credit","main_category":"Income","merchant":"Employer"},
        {"transaction_date":"2026-10-05","amount":200,"transaction_type":"expense","main_category":"Food","merchant":"Cafe"},
    ]
    result = generate_behavior_insights(rows, as_of="2026-10-20")
    assert result["summary"]["transaction_count"] == 1
    assert result["top_merchants"] == [{"merchant":"Cafe","transaction_count":1,"spending":200.0,"share_percentage":100.0}]


def test_excludes_flagged_transfers():
    rows = [
        {"transaction_date":"2026-10-03","amount":500,"transaction_type":"expense","main_category":"Food","exclude_from_expense_total":True},
        {"transaction_date":"2026-10-04","amount":200,"transaction_type":"expense","main_category":"Food"},
    ]
    result = generate_behavior_insights(rows, as_of="2026-10-20")
    assert result["summary"]["transaction_count"] == 1


def test_empty_input():
    result = generate_behavior_insights([])
    assert result["summary"]["transaction_count"] == 0
    assert result["insights"] == []


def test_missing_required_columns():
    with pytest.raises(ValueError, match="Missing required columns"):
        generate_behavior_insights([{"amount":100}])


def test_only_month_selected_for_monthly_behaviour():
    rows = [
        {"transaction_date":"2026-09-01","amount":10,"transaction_type":"expense","merchant":"Old Merchant"},
        {"transaction_date":"2026-10-01","amount":20,"transaction_type":"expense","merchant":"Current Merchant"},
    ]
    result = generate_behavior_insights(rows, as_of="2026-10-20")
    assert [x["merchant"] for x in result["top_merchants"]] == ["Current Merchant"]
    assert result["summary"]["transaction_count"] == 1
