from src.statement_parser import extract_phonepe_transactions
from src.transaction_classifier import classify_transaction


def process_phonepe_statement(pdf_bytes):

    transactions = extract_phonepe_transactions(pdf_bytes)

    processed_transactions = []

    for transaction in transactions:

        classification = classify_transaction(
            counterparty=transaction["merchant"]
        )

        transaction["category"] = classification["category"]

        transaction["classification_method"] = (
            classification["classification_method"]
        )

        transaction["needs_review"] = (
            classification["needs_review"]
        )

        processed_transactions.append(transaction)

    total_expenses = sum(
        t["amount"]
        for t in processed_transactions
        if t["transaction_type"] == "expense"
    )

    total_credits = sum(
        t["amount"]
        for t in processed_transactions
        if t["transaction_type"] == "credit"
    )

    return {
        "total_transactions": len(processed_transactions),
        "total_expenses": round(total_expenses, 2),
        "total_credits": round(total_credits, 2),
        "transactions_needing_review": sum(
            1 for t in processed_transactions
            if t["needs_review"]
        ),
        "transactions": processed_transactions
    }
