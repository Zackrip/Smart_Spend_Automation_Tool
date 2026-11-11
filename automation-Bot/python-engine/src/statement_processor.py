from src.statement_parser import extract_phonepe_transactions
from src.transaction_classifier import classify_transaction
from src.transaction_type_detector import detect_transaction_type


def process_phonepe_statement(pdf_bytes, user_id=None):
    """
    Extract PhonePe transactions and enrich each transaction with:
    main category, subcategory, confidence, review flag and transaction subtype.

    This function does not write statement transactions to PostgreSQL.
    """
    transactions = extract_phonepe_transactions(pdf_bytes)
    processed_transactions = []

    for transaction in transactions:
        description = transaction.get("transaction_description") or transaction.get("merchant") or ""
        merchant = transaction.get("merchant") or "Unknown"
        direction = transaction.get("transaction_type")

        classification = classify_transaction(
            counterparty=merchant,
            transaction_description=description,
            user_id=user_id,
            transaction_type=direction
        )

        detected_type = detect_transaction_type(
            description=description,
            direction=direction
        )

        transaction["category"] = classification["category"]
        transaction["main_category"] = classification["main_category"]
        transaction["subcategory"] = classification["subcategory"]
        transaction["classification_method"] = classification["classification_method"]
        transaction["confidence"] = classification["confidence"]
        transaction["transaction_type"] = detected_type["transaction_type"]
        transaction["transaction_subtype"] = detected_type["transaction_subtype"]
        transaction["needs_review"] = (
            classification["needs_review"]
            or detected_type["transaction_type"] == "unknown"
        )

        processed_transactions.append(transaction)

    total_expenses = sum(
        t["amount"] for t in processed_transactions
        if t["transaction_type"] == "expense"
    )

    total_credits = sum(
        t["amount"] for t in processed_transactions
        if t["transaction_type"] == "credit"
    )

    return {
        "total_transactions": len(processed_transactions),
        "total_expenses": round(total_expenses, 2),
        "total_credits": round(total_credits, 2),
        "transactions_needing_review": sum(
            1 for t in processed_transactions if t["needs_review"]
        ),
        "transactions": processed_transactions
    }
