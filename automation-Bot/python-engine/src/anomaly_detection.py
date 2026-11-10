import pandas as pd
def detect_expense_anomalies(
    transactions: pd.DataFrame,
    min_transactions: int = 4
) -> pd.DataFrame:
    required_columns = {
        "id", "user_id", "category_id", "amount"
    }
    missing_columns = required_columns - set(transactions.columns)
    if missing_columns:
        raise ValueError(
            f"Missing columns: {sorted(missing_columns)}"
        )
    df = transactions.copy()
    df["amount"] = pd.to_numeric(
        df["amount"], errors="coerce")
    df = df[
        df["amount"].notna() & (df["amount"] > 0)
    ].copy()
    group_cols = ["user_id", "category_id"]
    grouped = df.groupby(group_cols)["amount"]
    df["Q1"] = grouped.transform(
        lambda values: values.quantile(0.25))
    df["Q3"] = grouped.transform(
        lambda values: values.quantile(0.75))
    df["IQR"] = df["Q3"] - df["Q1"]
    df["upper_bound"] = (
        df["Q3"] + 1.5 * df["IQR"])
    df["group_size"] = grouped.transform("size")
    df["anomaly"] = (
        (df["amount"] > df["upper_bound"])
        & (df["group_size"] >= min_transactions))
    return df
