import pandas as pd
from src.anomaly_detection import detect_expense_anomalies
def test_anomaly_detection_flags_high_expense():
    transactions = pd.DataFrame({
        "id": [1, 2, 3, 4, 5],
        "user_id": [1, 1, 1, 1, 1],
        "category_id": [10, 10, 10, 10, 10],
        "amount": [100, 110, 105, 95, 1000],
    })
    result = detect_expense_anomalies(transactions)
    flagged = result.loc[result["anomaly"], "id"].tolist()
    assert 5 in flagged
def test_anomaly_detection_rejects_missing_columns():
    transactions = pd.DataFrame({
        "user_id": [1],
        "amount": [100],
    })
    try:
        detect_expense_anomalies(transactions)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError for missing columns")



import pandas as pd
from src.expense_forecasting import forecast_monthly_expenses
def test_forecast_uses_last_three_months():
    monthly_data = pd.DataFrame({
        "user_id": [1, 1, 1, 1],
        "month": pd.to_datetime([
            "2026-01-01",
            "2026-02-01",
            "2026-03-01",
            "2026-04-01",]),
        "monthly_expense": [1000, 2000, 3000, 4000],})
    result = forecast_monthly_expenses(
        monthly_data, window=3)
    assert len(result) == 1
    assert result.iloc[0]["forecast_expense"] == 3000.00
    assert result.iloc[0]["forecast_month"] == pd.Timestamp("2026-05-01")
def test_forecast_skips_insufficient_history():
    monthly_data = pd.DataFrame({
        "user_id": [1, 1],
        "month": pd.to_datetime([
            "2026-01-01",
            "2026-02-01",]),
        "monthly_expense": [1000, 2000],})
    result = forecast_monthly_expenses(
        monthly_data, window=3)
    assert result.empty


import pandas as pd
from src.budget_analysis import analyze_budgets
def test_budget_analysis_calculates_utilization():
    budgets = pd.DataFrame({
        "user_id": [1],
        "category_id": [10],
        "amount_limit": [5000],
        "start_date": ["2026-06-01"],
        "end_date": ["2026-06-30"],
    })
    transactions = pd.DataFrame({
        "user_id": [1, 1],
        "category_id": [10, 10],
        "amount": [2000, 2200],
        "transaction_type": ["expense", "expense"],
        "transaction_date": [
            "2026-06-10",
            "2026-06-20",],})
    categories = pd.DataFrame({
        "id": [10],
        "name": ["Groceries"],})
    result = analyze_budgets(
        budgets, transactions, categories)
    assert result.iloc[0]["actual_spending"] == 4200
    assert result.iloc[0]["remaining_budget"] == 800
    assert result.iloc[0]["utilization_pct"] == 84
    assert result.iloc[0]["budget_status"] == "Near Limit"
def test_budget_analysis_rejects_zero_budget():
    budgets = pd.DataFrame({
        "user_id": [1],
        "category_id": [10],
        "amount_limit": [0],
        "start_date": ["2026-06-01"],
        "end_date": ["2026-06-30"],})
    transactions = pd.DataFrame(columns=[
        "user_id", "category_id", "amount",
        "transaction_type", "transaction_date"])
    categories = pd.DataFrame({
        "id": [10],
        "name": ["Groceries"],})
    try:
        analyze_budgets(budgets, transactions, categories)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError for zero budget")


import pandas as pd
from src.savings_recommendations import analyze_savings_goals
def test_savings_goal_progress_calculation():
    savings_goals = pd.DataFrame({
        "user_id": [1],
        "name": ["Emergency Fund"],
        "target_amount": [50000],
        "current_amount": [20000],
        "target_date": ["2027-06-30"],
        "status": ["active"],})
    result = analyze_savings_goals(savings_goals)
    assert result.iloc[0]["remaining_amount"] == 30000
    assert result.iloc[0]["progress_pct"] == 40
    assert result.iloc[0]["goal_progress_status"] == "In Progress"
def test_savings_goal_rejects_zero_target():
    savings_goals = pd.DataFrame({
        "user_id": [1],
        "name": ["Emergency Fund"],
        "target_amount": [0],
        "current_amount": [0],
        "target_date": ["2027-06-30"],
        "status": ["active"],})
    try:
        analyze_savings_goals(savings_goals)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError for zero target")

