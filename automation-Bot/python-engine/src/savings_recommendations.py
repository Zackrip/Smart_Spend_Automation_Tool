import pandas as pd
def analyze_savings_goals(
    savings_goals: pd.DataFrame
) -> pd.DataFrame:
    """
    Calculate savings goal progress and generate
    practical recommendations for each goal.
    """
    required_columns = {
        "user_id",
        "name",
        "target_amount",
        "current_amount",
        "target_date",
        "status",
    }
    missing_columns = required_columns - set(
        savings_goals.columns
    )
    if missing_columns:
        raise ValueError(
            f"Missing columns: {sorted(missing_columns)}"
        )
    result = savings_goals.copy()
    # Convert amounts to numeric values
    result["target_amount"] = pd.to_numeric(
        result["target_amount"], errors="coerce"
    )
    result["current_amount"] = pd.to_numeric(
        result["current_amount"], errors="coerce"
    )
    if (
        result["target_amount"].isna().any()
        or result["current_amount"].isna().any()
    ):
        raise ValueError(
            "Target and current amounts must be numeric."
        )
    if (result["target_amount"] <= 0).any():
        raise ValueError(
            "Target amounts must be greater than zero."
        )
    if (result["current_amount"] < 0).any():
        raise ValueError(
            "Current saved amounts cannot be negative."
        )
    # Convert target dates to UTC
    result["target_date"] = pd.to_datetime(
        result["target_date"],
        errors="coerce",
        utc=True,
    )
    # Calculate remaining amount and progress
    result["remaining_amount"] = (
        result["target_amount"]
        - result["current_amount"]
    ).clip(lower=0)
    result["progress_pct"] = (
        result["current_amount"]
        / result["target_amount"]
        * 100
    )
    # Classify savings progress
    def classify_goal(row):
        if row["current_amount"] >= row["target_amount"]:
            return "Achieved"
        elif row["progress_pct"] >= 75:
            return "On Track"
        elif row["progress_pct"] >= 25:
            return "In Progress"
        return "Needs Attention"

    result["goal_progress_status"] = result.apply(
        classify_goal, axis=1
    )
    # Generate recommendations
    today = pd.Timestamp.now(tz="UTC").normalize()
    def generate_recommendation(row):
        name = row["name"]
        remaining = row["remaining_amount"]
        progress = row["progress_pct"]
        target_date = row["target_date"]
        if remaining <= 0:
            return (
                f"Congratulations! You have achieved "
                f"your {name} goal."
            )
        if pd.isna(target_date):
            return (
                f"You need ₹{remaining:,.2f} more for "
                f"{name}. Set a target date and savings plan."
            )
        days_left = (
            target_date.normalize() - today
        ).days
        if days_left <= 0:
            return (
                f"The target date for {name} has passed. "
                f"Review your plan for the remaining "
                f"₹{remaining:,.2f}."
            )
        months_left = days_left / 30.4375
        monthly_saving_needed = remaining / months_left
        if progress < 25:
            action = "Start saving consistently."
        elif progress < 75:
            action = "Continue saving and review progress monthly."
        else:
            action = "You're close to your goal; maintain your routine."
        return (
            f"{action} To reach {name} by the target date, "
            f"aim to save approximately "
            f"₹{monthly_saving_needed:,.2f} per month.")
    result["recommendation"] = result.apply(
        generate_recommendation, axis=1)
    return result
