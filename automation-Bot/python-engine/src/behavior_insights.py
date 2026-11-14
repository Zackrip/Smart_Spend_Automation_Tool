
"""Explainable transaction-behaviour insights for Paisora."""

import pandas as pd


def _empty_result():
    return {
        "summary": {
            "period": None,
            "transaction_count": 0,
            "date_from": None,
            "date_to": None,
            "history_date_from": None,
            "history_date_to": None
        },
        "insights": [],
        "metrics": {},
        "top_merchants": [],
        "category_frequency": []
    }


def generate_behavior_insights(
    transactions,
    as_of=None,
    small_transaction_threshold=100,
    frequent_merchant_min_count=5,
    top_n=5,
    min_weekend_active_days=2,
    min_weekday_active_days=4
):
    """Generate frequency, merchant concentration, weekend and small-payment insights."""

    df = pd.DataFrame(transactions).copy()

    required = {
        "transaction_date",
        "amount",
        "transaction_type"
    }

    if df.empty:
        return _empty_result()

    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}"
        )

    df["transaction_date"] = pd.to_datetime(
        df["transaction_date"], errors="coerce"
    )

    df["amount"] = pd.to_numeric(
        df["amount"], errors="coerce"
    )

    df = df[
        df["transaction_date"].notna()
        & df["amount"].notna()
        & (df["amount"] > 0)
        & (
            df["transaction_type"]
            .astype(str)
            .str.lower() == "expense"
        )
    ].copy()

    if "exclude_from_expense_total" in df.columns:
        excluded = df["exclude_from_expense_total"].map(
            lambda x: x is True
            or str(x).strip().lower() in {"true", "1", "yes"}
        )

        df = df[~excluded].copy()

    category_col = (
        "main_category"
        if "main_category" in df.columns
        else "category"
    )

    if category_col in df.columns:
        df = df[
            df[category_col]
            .fillna("")
            .astype(str)
            .str.lower() != "personal transfers"
        ].copy()

    if df.empty:
        return _empty_result()

    df["_weekday"] = df["transaction_date"].dt.dayofweek
    df["_is_weekend"] = df["_weekday"] >= 5
    df["_month"] = df["transaction_date"].dt.to_period("M")

    report_period = (
        pd.Timestamp(as_of)
        if as_of is not None
        else df["transaction_date"].max()
    ).to_period("M")

    month_df = df[
        df["_month"] == report_period
    ].copy()

    insights = []
    metrics = {}

    # 1. Small transactions

    month_count = int(len(month_df))

    metrics["current_month_transaction_count"] = month_count

    small = month_df[
        month_df["amount"] < float(small_transaction_threshold)
    ]

    small_count = int(len(small))
    small_total = float(small["amount"].sum())

    metrics["small_transaction_threshold"] = float(
        small_transaction_threshold
    )

    metrics["small_transaction_count"] = small_count
    metrics["small_transaction_total"] = round(small_total, 2)

    if small_count >= 5:
        insights.append({
            "insight_type": "frequent_small_transactions",
            "period": str(report_period),
            "transaction_count": small_count,
            "total_amount": round(small_total, 2),
            "threshold": float(small_transaction_threshold),
            "message": (
                f"You made {small_count} transactions "
                f"below ₹{small_transaction_threshold:g} this month."
            ),
            "recommendation": (
                "Review these smaller purchases together "
                "to see whether any are avoidable."
            )
        })

    # 2. Merchant frequency and concentration

    top_merchants = []

    if "merchant" in month_df.columns:

        m = month_df.copy()

        m["merchant"] = (
            m["merchant"].fillna("").astype(str).str.strip()
        )

        m = m[m["merchant"] != ""]

        if not m.empty:

            grouped = m.groupby("merchant").agg(
                transaction_count=("amount", "size"),
                spending=("amount", "sum")
            ).sort_values(
                ["spending", "transaction_count"],
                ascending=False
            )

            month_total = float(month_df["amount"].sum())

            for merchant, row in grouped.head(top_n).iterrows():

                share = (
                    float(row["spending"]) / month_total * 100
                    if month_total else 0
                )

                top_merchants.append({
                    "merchant": str(merchant),
                    "transaction_count": int(row["transaction_count"]),
                    "spending": round(float(row["spending"]), 2),
                    "share_percentage": round(share, 2)
                })

                if int(row["transaction_count"]) >= frequent_merchant_min_count:

                    insights.append({
                        "insight_type": "frequent_merchant",
                        "merchant": str(merchant),
                        "period": str(report_period),
                        "transaction_count": int(row["transaction_count"]),
                        "spending": round(float(row["spending"]), 2),
                        "message": (
                            f"You made {int(row['transaction_count'])} "
                            f"payments to {merchant} this month."
                        ),
                        "recommendation": (
                            f"Check whether this payment frequency "
                            f"at {merchant} matches your needs."
                        )
                    })

                if share >= 40:

                    insights.append({
                        "insight_type": "merchant_spending_concentration",
                        "merchant": str(merchant),
                        "period": str(report_period),
                        "share_percentage": round(share, 2),
                        "spending": round(float(row["spending"]), 2),
                        "message": (
                            f"{share:.1f}% of this month's recorded "
                            f"expenses went to {merchant}."
                        ),
                        "recommendation": (
                            "Review this merchant's transactions "
                            "to understand the concentration."
                        )
                    })

    # 3. Weekend versus weekday comparison

    if not month_df.empty:

        weekend_total = float(
            month_df.loc[month_df["_is_weekend"], "amount"].sum()
        )

        weekday_total = float(
            month_df.loc[~month_df["_is_weekend"], "amount"].sum()
        )

        weekend_days = int(
            month_df.loc[
                month_df["_is_weekend"], "transaction_date"
            ].dt.date.nunique()
        )

        weekday_days = int(
            month_df.loc[
                ~month_df["_is_weekend"], "transaction_date"
            ].dt.date.nunique()
        )

        weekend_avg = (
            weekend_total / weekend_days if weekend_days else 0
        )

        weekday_avg = (
            weekday_total / weekday_days if weekday_days else 0
        )

        comparison_available = (
            weekend_days >= min_weekend_active_days
            and weekday_days >= min_weekday_active_days
        )

        metrics.update({
            "weekend_spending": round(weekend_total, 2),
            "weekday_spending": round(weekday_total, 2),
            "weekend_active_days": weekend_days,
            "weekday_active_days": weekday_days,
            "weekend_average_per_active_day": round(weekend_avg, 2),
            "weekday_average_per_active_day": round(weekday_avg, 2),
            "weekend_comparison_available": comparison_available,
            "minimum_weekend_active_days": min_weekend_active_days,
            "minimum_weekday_active_days": min_weekday_active_days
        })

        if (
            comparison_available
            and weekday_avg > 0
            and weekend_avg >= weekday_avg * 1.25
        ):

            ratio = (
                (weekend_avg / weekday_avg - 1) * 100
            )

            insights.append({
                "insight_type": "weekend_spending_higher",
                "period": str(report_period),
                "weekend_average_per_active_day": round(weekend_avg, 2),
                "weekday_average_per_active_day": round(weekday_avg, 2),
                "change_percentage": round(ratio, 2),
                "message": (
                    f"Your average spending per active weekend day "
                    f"is {ratio:.1f}% higher than on active weekdays."
                ),
                "recommendation": (
                    "Review weekend purchases to see whether "
                    "you want to set a separate weekend budget."
                )
            })

    # 4. Category transaction frequency

    category_frequency = []

    if category_col in month_df.columns and not month_df.empty:

        grouped = month_df.groupby(category_col).agg(
            transaction_count=("amount", "size"),
            spending=("amount", "sum")
        ).sort_values(
            "transaction_count",
            ascending=False
        )

        category_frequency = [
            {
                "category": str(k),
                "transaction_count": int(v["transaction_count"]),
                "spending": round(float(v["spending"]), 2)
            }
            for k, v in grouped.head(top_n).iterrows()
        ]

    # 5. Final result

    return {
        "summary": {
            "period": str(report_period),
            "transaction_count": month_count,
            "date_from": (
                month_df["transaction_date"].min().date().isoformat()
                if not month_df.empty else None
            ),
            "date_to": (
                month_df["transaction_date"].max().date().isoformat()
                if not month_df.empty else None
            ),
            "history_date_from": (
                df["transaction_date"].min().date().isoformat()
            ),
            "history_date_to": (
                df["transaction_date"].max().date().isoformat()
            )
        },
        "metrics": metrics,
        "top_merchants": top_merchants,
        "category_frequency": category_frequency,
        "insights": insights
    }
