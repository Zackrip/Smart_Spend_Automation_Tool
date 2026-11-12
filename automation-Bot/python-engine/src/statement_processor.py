
from src.statement_parser import extract_phonepe_transactions
from src.transaction_classifier import classify_transaction
from src.transaction_type_detector import detect_transaction_type
from src.personal_transfer_classifier import classify_personal_transfer


def process_phonepe_statement(pdf_bytes, user_id=None):
    """
    Extract and classify PhonePe statement transactions.

    Classification priority:
    1. Known merchant / business
    2. Confirmed personal transfer
    3. Other / Uncategorised

    This function does not persist transactions to PostgreSQL.
    """

    transactions = extract_phonepe_transactions(pdf_bytes)
    processed_transactions = []

    for transaction in transactions:

        merchant = transaction.get("merchant") or "Unknown"

        description = (
            transaction.get("transaction_description")
            or transaction.get("description")
            or merchant
        )

        direction = transaction.get("transaction_type")

        # -----------------------------------------
        # STEP 1: CLASSIFY MERCHANT FIRST
        # -----------------------------------------

        classification = classify_transaction(
            counterparty=merchant,
            transaction_description=description,
            user_id=user_id,
            transaction_type=direction
        )

        # -----------------------------------------
        # STEP 2: CHECK PERSONAL TRANSFER
        # ONLY IF MERCHANT IS NOT IDENTIFIED
        # -----------------------------------------

        if classification.get("main_category") == "Other":

            personal = classify_personal_transfer(
                counterparty=merchant,
                description=description,
                direction=direction,
                user_id=user_id
            )

            if personal is not None:
                classification = personal

        # -----------------------------------------
        # STEP 3: DETECT TRANSACTION TYPE
        # -----------------------------------------

        detected_type = detect_transaction_type(
            description=description,
            direction=direction
        )

        transaction_type = detected_type.get(
            "transaction_type", "unknown"
        )

        # -----------------------------------------
        # STEP 4: UPDATE TRANSACTION
        # -----------------------------------------

        transaction["category"] = classification.get(
            "category", "Other"
        )

        transaction["main_category"] = classification.get(
            "main_category", "Other"
        )

        transaction["subcategory"] = classification.get(
            "subcategory", "Uncategorised"
        )

        transaction["classification_method"] = classification.get(
            "classification_method", "unknown"
        )

        transaction["confidence"] = classification.get(
            "confidence", 0.0
        )

        transaction["transaction_type"] = transaction_type

        transaction["transaction_subtype"] = (
            classification.get("transaction_subtype")
            or detected_type.get("transaction_subtype")
        )

        transaction["needs_review"] = (
            classification.get("needs_review", True)
            or transaction_type == "unknown"
        )

        processed_transactions.append(transaction)

    # -----------------------------------------
    # STEP 5: CALCULATE TOTALS
    # -----------------------------------------

    total_expenses = sum(
        float(t.get("amount") or 0)
        for t in processed_transactions
        if t.get("transaction_type") == "expense"
    )

    total_credits = sum(
        float(t.get("amount") or 0)
        for t in processed_transactions
        if t.get("transaction_type") == "credit"
    )

    transactions_needing_review = sum(
        1
        for t in processed_transactions
        if t.get("needs_review")
    )

    return {
        "total_transactions": len(processed_transactions),
        "total_expenses": round(total_expenses, 2),
        "total_credits": round(total_credits, 2),
        "transactions_needing_review": transactions_needing_review,
        "transactions": processed_transactions
    }
