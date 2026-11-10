import pandas as pd
def analyze_budgets(
    budgets: pd.DataFrame,
    transactions: pd.DataFrame,
    categories: pd.DataFrame,
    near_limit_pct: float = 80.0
) -> pd.DataFrame:
    """
    Calculate spending, remaining budget, utilization,
    status, and a readable financial insight per budget.
    """
    budget_required = {
        "user_id", "category_id", "amount_limit",
        "start_date", "end_date"}
    transaction_required = {
        "user_id", "category_id", "amount",
        "transaction_type", "transaction_date"}
    category_required = {"id", "name"}
    if not budget_required.issubset(budgets.columns):
        raise ValueError("Budgets DataFrame is missing required columns.")
    if not transaction_required.issubset(transactions.columns):
        raise ValueError("Transactions DataFrame is missing required columns.")
    if not category_required.issubset(categories.columns):
        raise ValueError("Categories DataFrame is missing id or name.")
    result = budgets.copy()
    tx = transactions.copy()
    result["start_date"] = pd.to_datetime(result["start_date"], utc=True)
    result["end_date"] = pd.to_datetime(result["end_date"], utc=True)
    tx["transaction_date"] = pd.to_datetime(
        tx["transaction_date"], utc=True)
    result["amount_limit"] = pd.to_numeric(
        result["amount_limit"], errors="coerce")
    tx["amount"] = pd.to_numeric(tx["amount"], errors="coerce")
    if result["amount_limit"].isna().any() or (
        result["amount_limit"] <= 0
    ).any():
        raise ValueError("Budget limits must be positive numeric values.")
    tx = tx[
        (tx["transaction_type"] == "expense")
        & tx["amount"].notna()
        & (tx["amount"] > 0)
    ].copy()
    spending = []
    for _, budget in result.iterrows():
        matching = tx[
            (tx["user_id"] == budget["user_id"])
            & (tx["category_id"] == budget["category_id"])
            & (tx["transaction_date"] >= budget["start_date"])
            & (
                tx["transaction_date"]
                < budget["end_date"] + pd.Timedelta(days=1))]
        spending.append(matching["amount"].sum())
    result["actual_spending"] = spending
    result["remaining_budget"] = (
        result["amount_limit"] - result["actual_spending"])
    result["utilization_pct"] = (
        result["actual_spending"] / result["amount_limit"] * 100)
    def classify(value):
        if value > 100:
            return "Exceeded"
        if value >= near_limit_pct:
            return "Near Limit"
        return "Within Budget"
    result["budget_status"] = result["utilization_pct"].apply(classify)
    category_map = categories.set_index("id")["name"].to_dict()
    def make_insight(row):
        name = category_map.get(
            row["category_id"], f"Category {row['category_id']}")
        if row["budget_status"] == "Exceeded":
            return (
                f"Your {name} spending reached ₹{row['actual_spending']:.2f} "
                f"against a ₹{row['amount_limit']:.2f} budget. "
                f"You exceeded it by ₹{-row['remaining_budget']:.2f}.")
        if row["budget_status"] == "Near Limit":
            return (
                f"You have used {row['utilization_pct']:.1f}% of your "
                f"{name} budget. ₹{row['remaining_budget']:.2f} remains.")
        return (
            f"Your {name} spending is within budget. "
            f"₹{row['remaining_budget']:.2f} remains.")
    result["financial_insight"] = result.apply(make_insight, axis=1)
    return result
