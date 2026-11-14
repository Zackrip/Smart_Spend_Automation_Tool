import pytest
from src.spending_insights import generate_spending_insights

@pytest.fixture
def rows():
    return [
      {"transaction_date":"2026-08-05","amount":1000,"transaction_type":"expense","main_category":"Food","merchant":"Swiggy"},
      {"transaction_date":"2026-09-05","amount":3000,"transaction_type":"expense","main_category":"Food","merchant":"Swiggy"},
      {"transaction_date":"2026-09-10","amount":2000,"transaction_type":"expense","main_category":"Travel","merchant":"Uber"},
      {"transaction_date":"2026-10-05","amount":4500,"transaction_type":"expense","main_category":"Food","merchant":"Zomato"},
      {"transaction_date":"2026-10-10","amount":2000,"transaction_type":"expense","main_category":"Travel","merchant":"Uber"},
    ]

def test_monthly_and_all_time_outputs(rows):
    r=generate_spending_insights(rows,as_of="2026-10-20")
    assert set(r)=={"monthly","all_time"}
    assert r["monthly"]["summary"]["current_month_spending"]==6500
    assert r["monthly"]["summary"]["previous_month_spending"]==5000
    assert r["monthly"]["summary"]["change_percentage"]==30
    assert r["all_time"]["summary"]["total_spending"]==12500
    assert r["all_time"]["summary"]["transaction_count"]==5

def test_all_time_category_share(rows):
    r=generate_spending_insights(rows,as_of="2026-10-20")
    food=next(x for x in r["all_time"]["category_breakdown"] if x["category"]=="Food")
    assert food["spending"]==8500 and food["share_percentage"]==68

def test_top_merchants(rows):
    r=generate_spending_insights(rows,as_of="2026-10-20")
    assert r["all_time"]["top_merchants"][0]=={"merchant":"Zomato","spending":4500.0}

def test_credits_and_excluded_transfers_ignored():
    rows=[
      {"transaction_date":"2026-09-10","amount":1000,"transaction_type":"expense","main_category":"Food"},
      {"transaction_date":"2026-10-10","amount":5000,"transaction_type":"credit","main_category":"Income"},
      {"transaction_date":"2026-10-11","amount":9000,"transaction_type":"expense","main_category":"Personal Transfers","exclude_from_expense_total":True},
      {"transaction_date":"2026-10-12","amount":1200,"transaction_type":"expense","main_category":"Food"}]
    r=generate_spending_insights(rows,as_of="2026-10-20")
    assert r["monthly"]["summary"]["current_month_spending"]==1200
    assert r["all_time"]["summary"]["total_spending"]==2200

def test_no_previous_month_percentage():
    r=generate_spending_insights([{"transaction_date":"2026-10-10","amount":1200,"transaction_type":"expense","main_category":"Food"}],as_of="2026-10-20")
    assert r["monthly"]["summary"]["change_percentage"] is None

def test_empty_result():
    r=generate_spending_insights([])
    assert r["monthly"]["insights"]==[] and r["all_time"]["summary"]["total_spending"]==0

def test_missing_fields():
    with pytest.raises(ValueError,match="Missing required columns"):
        generate_spending_insights([{"amount":100}])

def test_all_time_date_range(rows):
    r=generate_spending_insights(rows,as_of="2026-10-20")
    assert r["all_time"]["summary"]["date_from"]=="2026-08-05"
    assert r["all_time"]["summary"]["date_to"]=="2026-10-10"
