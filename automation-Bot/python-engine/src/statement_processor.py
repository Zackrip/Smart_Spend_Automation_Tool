from src.statement_parser import extract_phonepe_transactions
from src.transaction_classifier import classify_transaction
from src.transaction_type_detector import detect_transaction_type
from src.personal_transfer_classifier import classify_personal_transfer
from src.counterparty_detector import detect_counterparty
from src.phonepe_special_rules import (
    detect_phonepe_special_case,
    detect_payment_source,
)

def _base_classification():
    return {
        "category": "Other",
        "main_category": "Other",
        "subcategory": "Uncategorised",
        "classification_method": "unknown",
        "confidence": 0.0,
        "needs_review": True,
    }

def process_phonepe_statement(pdf_bytes, user_id=None):
    """Parse and classify PhonePe statement rows. Does not persist to PostgreSQL."""
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

        # 1. Special financial events take priority over merchant classification.
        special = detect_phonepe_special_case(transaction)
        if special:
            classification = special.copy()
        else:
            # 2. Known merchant/business classification takes priority over P2P.
            classification = classify_transaction(
                counterparty=merchant,
                transaction_description=description,
                user_id=user_id,
                transaction_type=direction,
            ) or _base_classification()

            # 3. Only try personal-transfer logic when merchant rules found no
            # meaningful business category.
            if classification.get("main_category") == "Other":
                personal = classify_personal_transfer(
                    counterparty=merchant,
                    description=description,
                    direction=direction,
                    user_id=user_id,
                )
                if personal is not None:
                    classification = personal

            # 4. If still unknown, detect a possible human counterparty.
            if classification.get("main_category") == "Other":
                candidate = detect_counterparty(merchant, description)
                if candidate["is_person_candidate"]:
                    flow = candidate["transfer_direction"]
                    classification = {
                        "category": "Personal Transfers",
                        "main_category": "Personal Transfers",
                        "subcategory": "Person-to-Person",
                        "transaction_subtype": (
                            "p2p_incoming" if flow == "incoming" else "p2p_outgoing"
                        ),
                        "classification_method": "person_name_transfer_candidate",
                        "confidence": candidate["confidence"],
                        "needs_review": True,
                        "counterparty_name": candidate["counterparty_name"],
                        "exclude_from_expense_total": False,
                        "exclude_from_income_total": True,
                        "is_internal_transfer": False,
                    }

        # 5. Direction and subtype detection. Do not overwrite special-case types.
        detected_type = detect_transaction_type(description, direction)
        transaction_type = classification.get(
            "transaction_type", detected_type["transaction_type"]
        )
        transaction_subtype = classification.get(
            "transaction_subtype", detected_type["transaction_subtype"]
        )

        transaction.update({
            "category": classification.get("category", "Other"),
            "main_category": classification.get("main_category", "Other"),
            "subcategory": classification.get("subcategory", "Uncategorised"),
            "classification_method": classification.get("classification_method", "unknown"),
            "confidence": classification.get("confidence", 0.0),
            "transaction_type": transaction_type,
            "transaction_subtype": transaction_subtype,
            "needs_review": (
                bool(classification.get("needs_review", True))
                or transaction_type == "unknown"
            ),
            "payment_source": detect_payment_source(transaction),
            "is_internal_transfer": bool(classification.get("is_internal_transfer", False)),
            "exclude_from_expense_total": bool(
                classification.get("exclude_from_expense_total", False)
            ),
            "exclude_from_income_total": bool(
                classification.get("exclude_from_income_total", False)
            ),
        })

        if classification.get("counterparty_name"):
            transaction["counterparty_name"] = classification["counterparty_name"]

        transaction["is_p2p"] = transaction_subtype in {
            "p2p_incoming", "p2p_outgoing"
        }
        processed_transactions.append(transaction)

    total_expenses = sum(
        float(t.get("amount") or 0)
        for t in processed_transactions
        if t.get("transaction_type") == "expense"
        and not t.get("exclude_from_expense_total")
    )
    total_credits = sum(
        float(t.get("amount") or 0)
        for t in processed_transactions
        if t.get("transaction_type") == "credit"
    )
    total_income = sum(
        float(t.get("amount") or 0)
        for t in processed_transactions
        if t.get("transaction_type") == "credit"
        and not t.get("exclude_from_income_total")
    )
    total_internal_transfers = sum(
        float(t.get("amount") or 0)
        for t in processed_transactions
        if t.get("transaction_type") == "transfer"
    )

    return {
        "total_transactions": len(processed_transactions),
        "total_expenses": round(total_expenses, 2),
        "total_credits": round(total_credits, 2),
        "total_income": round(total_income, 2),
        "total_internal_transfers": round(total_internal_transfers, 2),
        "transactions_needing_review": sum(
            1 for t in processed_transactions if t.get("needs_review")
        ),
        "unclassified_transactions": sum(
            1 for t in processed_transactions
            if t.get("main_category") == "Other"
        ),
        "awaiting_user_confirmation": sum(
            1 for t in processed_transactions
            if t.get("classification_method") == "person_name_transfer_candidate"
        ),
        "transactions": processed_transactions,
    }


def process_phonepe_statement(pdf_bytes, user_id=None):
    """Parse and classify a PhonePe PDF. Keeps the existing PDF entry point."""
    transactions = extract_phonepe_transactions(pdf_bytes)
    return process_phonepe_transactions(transactions, user_id=user_id)
