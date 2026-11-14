
import pandas as pd


def _empty():
    return {
        "monthly": {
            "summary": {
                "current_month": None,
                "previous_month": None,
                "current_month_spending": 0.0,
                "previous_month_spending": 0.0,
                "change_amount": 0.0,
                "change_percentage": None
            },
            "top_categories": [],
            "insights": []
        },
        "all_time": {
            "summary": {
                "total_spending": 0.0,
                "transaction_count": 0,
                "average_transaction": 0.0,
                "date_from": None,
                "date_to": None
            },
            "category_breakdown": [],
            "top_merchants": [],
            "insights": []
        }
    }


def generate_spending_insights(
    transactions,
    as_of=None,
    top_n=3,
    low_baseline_threshold=500
):
    """
    Return monthly comparisons and all-time analysis
    of recorded expenses.
    """

    # ---------------------------------------
    # 1. DATA PREPARATION
    # ---------------------------------------

    df = pd.DataFrame(transactions).copy()

    required = {
        "transaction_date",
        "amount",
        "transaction_type"
    }

    if df.empty:
        return _empty()

    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}"
        )

    df["transaction_date"] = pd.to_datetime(
        df["transaction_date"],
        errors="coerce"
    )

    df["amount"] = pd.to_numeric(
        df["amount"],
        errors="coerce"
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

    # Exclude transactions marked as transfers or
    # otherwise excluded from expense totals.

    if "exclude_from_expense_total" in df.columns:

        excluded = df["exclude_from_expense_total"].map(
            lambda x: (
                x is True
                or str(x).strip().lower()
                in {"true", "1", "yes"}
            )
        )

        df = df[~excluded].copy()

    if df.empty:
        return _empty()

    # ---------------------------------------
    # 2. CATEGORY PREPARATION
    # ---------------------------------------

    cat = (
        "main_category"
        if "main_category" in df.columns
        else "category"
    )

    if cat not in df.columns:
        df[cat] = "Uncategorised"

    df[cat] = (
        df[cat]
        .fillna("Uncategorised")
        .astype(str)
    )

    # ---------------------------------------
    # 3. ALL-TIME SPENDING ANALYSIS
    # ---------------------------------------

    total = float(df.amount.sum())

    cat_totals = (
        df.groupby(cat)["amount"]
        .sum()
        .sort_values(ascending=False)
    )

    breakdown = [
        {
            "category": str(k),
            "spending": round(float(v), 2),
            "share_percentage": round(
                float(v) / total * 100, 2
            )
        }
        for k, v in cat_totals.items()
    ]

    all_insights = []

    # Category concentration insight

    if breakdown and breakdown[0]["share_percentage"] >= 40:

        lead = breakdown[0]

        all_insights.append({
            "insight_type": "all_time_category_concentration",
            "category": lead["category"],
            "share_percentage": lead["share_percentage"],
            "message": (
                f'{lead["share_percentage"]:.1f}% of your '
                f'recorded expenses are in {lead["category"]}.'
            ),
            "recommendation": (
                "Review whether spending in this category "
                "matches your priorities."
            )
        })

    # Top merchants

    merchants = []

    if "merchant" in df.columns:

        m = df.copy()

        m["merchant"] = (
            m["merchant"]
            .fillna("")
            .astype(str)
            .str.strip()
        )

        m = m[m["merchant"] != ""]

        merchants = [
            {
                "merchant": str(k),
                "spending": round(float(v), 2)
            }
            for k, v in (
                m.groupby("merchant")["amount"]
                .sum()
                .sort_values(ascending=False)
                .head(top_n)
                .items()
            )
        ]

    all_time = {
        "summary": {
            "total_spending": round(total, 2),
            "transaction_count": int(len(df)),
            "average_transaction": round(
                total / len(df), 2
            ),
            "date_from": (
                df["transaction_date"]
                .min().date().isoformat()
            ),
            "date_to": (
                df["transaction_date"]
                .max().date().isoformat()
            )
        },
        "category_breakdown": breakdown,
        "top_merchants": merchants,
        "insights": all_insights
    }

    # ---------------------------------------
    # 4. MONTHLY SPENDING ANALYSIS
    # ---------------------------------------

    period = (
        pd.Timestamp(as_of)
        if as_of is not None
        else df["transaction_date"].max()
    ).to_period("M")

    prev = period - 1

    df["_month"] = (
        df["transaction_date"].dt.to_period("M")
    )

    cur = df[df["_month"] == period]
    old = df[df["_month"] == prev]

    ct = float(cur.amount.sum())
    pt = float(old.amount.sum())

    change = ct - pt

    pct = (
        round(change / pt * 100, 2)
        if pt > 0
        else None
    )

    # Category-wise monthly spending

    curcats = cur.groupby(cat)["amount"].sum()
    oldcats = old.groupby(cat)["amount"].sum()

    top = [
        {
            "category": str(k),
            "spending": round(float(v), 2)
        }
        for k, v in (
            curcats
            .sort_values(ascending=False)
            .head(top_n)
            .items()
        )
    ]

    insights = []

    # ---------------------------------------
    # 5. OVERALL MONTHLY SPENDING CHANGE
    # ---------------------------------------

    if pt > 0 and change != 0:

        increase = change > 0

        insights.append({
            "insight_type": (
                "monthly_spending_increase"
                if increase
                else "monthly_spending_decrease"
            ),
            "severity": (
                ("medium" if pct < 25 else "high")
                if increase
                else "positive"
            ),
            "current_spending": round(ct, 2),
            "previous_spending": round(pt, 2),
            "change_amount": round(change, 2),
            "change_percentage": pct,
            "message": (
                f'Your spending {"increased" if increase else "decreased"} '
                f'by {abs(pct):.1f}% compared with the previous month.'
            ),
            "recommendation": (
                "Review category-wise spending to understand the change."
                if increase
                else "Keep tracking your spending and maintain this progress."
            )
        })

    # ---------------------------------------
    # 6. CATEGORY-WISE SPENDING INCREASE
    # ---------------------------------------

    for category in sorted(
        set(curcats.index) | set(oldcats.index)
    ):

        now = float(curcats.get(category, 0))
        before = float(oldcats.get(category, 0))

        if before > 0 and now > before:

            delta = now - before
            cp = delta / before * 100

            low_baseline = (
                before < low_baseline_threshold
            )

            if cp >= 20 and delta >= 100:

                if low_baseline:

                    message = (
                        f"{category} spending increased by "
                        f"₹{delta:,.2f}, from ₹{before:,.2f} "
                        f"to ₹{now:,.2f}. "
                        "The percentage increase is unusually large "
                        "because previous-month spending was low."
                    )

                    severity = "info"

                    recommendation = (
                        f"Review your recent {category} purchases "
                        "to understand this increase."
                    )

                else:

                    message = (
                        f"Your {category} spending increased "
                        f"by {cp:.1f}%."
                    )

                    severity = (
                        "medium" if cp < 50 else "high"
                    )

                    recommendation = (
                        f"Review recent {category} transactions "
                        "to understand the increase."
                    )

                insights.append({
                    "insight_type": "category_spending_increase",
                    "category": str(category),
                    "current_spending": round(now, 2),
                    "previous_spending": round(before, 2),
                    "change_amount": round(delta, 2),
                    "change_percentage": round(cp, 2),
                    "low_previous_month_baseline": low_baseline,
                    "severity": severity,
                    "message": message,
                    "recommendation": recommendation
                })

    # ---------------------------------------
    # 7. FINAL MONTHLY RESULT
    # ---------------------------------------

    monthly = {
        "summary": {
            "current_month": str(period),
            "previous_month": str(prev),
            "current_month_spending": round(ct, 2),
            "previous_month_spending": round(pt, 2),
            "change_amount": round(change, 2),
            "change_percentage": pct
        },
        "top_categories": top,
        "insights": insights
    }

    # ---------------------------------------
    # 8. FINAL RESPONSE
    # ---------------------------------------

    return {
        "monthly": monthly,
        "all_time": all_time
    }
