import pandas as pd
def forecast_monthly_expenses(
    monthly_data: pd.DataFrame,
    window: int = 3
) -> pd.DataFrame:
    """
    Forecast each user's next monthly expense using
    the average of their last recorded monthly totals.
    """
    required_columns = {"user_id", "month", "monthly_expense"}
    missing_columns = required_columns - set(monthly_data.columns)
    if missing_columns:
        raise ValueError(
            f"Missing columns: {sorted(missing_columns)}")
    results = []
    for user_id, group in monthly_data.groupby("user_id"):
        group = group.sort_values("month")
        recent_expenses = group["monthly_expense"].tail(window)
        if len(recent_expenses) < window:
            continue
        last_month = pd.Timestamp(group["month"].max())
        next_month = last_month + pd.offsets.MonthBegin(1)
        predicted_expense = recent_expenses.mean()
        results.append({
            "user_id": user_id,
            "forecast_month": next_month,
            "forecast_expense": round(predicted_expense, 2),
            "history_months_used": window})
    return pd.DataFrame(results)
