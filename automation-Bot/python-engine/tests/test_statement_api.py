from decimal import Decimal

from src.statement_api import build_statement_overview


def test_overview_calculates_category_expenses_and_preserves_transactions():
    result = {
        "total_transactions": 3,
        "total_expenses": 150.50,
        "total_credits": 300,
        "total_income": 300,
        "total_internal_transfers": 0,
        "transactions_needing_review": 1,
        "unclassified_transactions": 1,
        "awaiting_user_confirmation": 0,
        "transactions": [
            {
                "amount": Decimal("100.50"),
                "transaction_type": "expense",
                "category": "Food",
                "exclude_from_expense_total": False,
            },
            {
                "amount": Decimal("50"),
                "transaction_type": "expense",
                "category": "Travel",
                "exclude_from_expense_total": False,
            },
            {
                "amount": Decimal("300"),
                "transaction_type": "credit",
                "category": "Income",
                "exclude_from_expense_total": False,
            },
        ],
    }

    overview = build_statement_overview(result)

    assert overview["summary"]["total_transactions"] == 3
    assert overview["summary"]["total_expenses"] == 150.50
    assert overview["category_wise_expenses"] == [
        {"category": "Food", "amount": 100.5},
        {"category": "Travel", "amount": 50.0},
    ]
    assert overview["transactions"][0]["amount"] == 100.5


def test_internal_transfers_excluded_from_category_expenses():
    result = {
        "transactions": [
            {
                "amount": Decimal("500"),
                "transaction_type": "expense",
                "category": "Personal Transfers",
                "exclude_from_expense_total": True,
            }
        ]
    }

    overview = build_statement_overview(result)

    assert overview["category_wise_expenses"] == []
    assert overview["summary"]["total_transactions"] == 1


def test_empty_result_returns_empty_overview():
    overview = build_statement_overview({"transactions": []})

    assert overview["summary"]["total_transactions"] == 0
    assert overview["category_wise_expenses"] == []
    assert overview["transactions"] == []
