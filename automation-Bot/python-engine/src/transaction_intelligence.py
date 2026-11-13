"""Phase 4 transaction intelligence orchestration and summary helpers."""
from src.merchant_intelligence import annotate_merchant_identity
from src.recurring_payment_detector import (
    detect_recurring_payment_candidates,
    annotate_recurring_payment_candidates,
)
from src.duplicate_detector import detect_duplicate_transactions
from src.review_queue import build_transaction_review_queue


def enrich_transaction_intelligence(transactions, confidence_threshold=0.70):
    annotate_merchant_identity(transactions)
    recurring = detect_recurring_payment_candidates(transactions)
    annotate_recurring_payment_candidates(transactions)
    duplicates = detect_duplicate_transactions(transactions)
    review_queue = build_transaction_review_queue(transactions, confidence_threshold)
    return {
        "transactions": transactions,
        "recurring_payments": recurring,
        "duplicate_candidates": duplicates,
        "review_queue": review_queue,
        "intelligence_summary": {
            "recurring_patterns_detected": len(recurring),
            "transactions_in_recurring_patterns": sum(x["occurrences"] for x in recurring),
            "duplicate_candidates": len(duplicates),
            "transactions_needing_review": len(review_queue),
            "low_confidence_threshold": confidence_threshold,
        },
    }
