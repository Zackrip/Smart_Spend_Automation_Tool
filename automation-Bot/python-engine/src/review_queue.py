"""Build a compact, prioritized transaction review queue."""


def build_transaction_review_queue(transactions, confidence_threshold=0.70):
    queue = []
    for index, tx in enumerate(transactions):
        confidence = tx.get("confidence")
        try:
            confidence = float(confidence)
        except (TypeError, ValueError):
            confidence = 0.0
        reasons = []
        if tx.get("needs_review"):
            reasons.append("classifier_requested_review")
        if confidence < confidence_threshold:
            reasons.append("low_confidence")
        if tx.get("is_duplicate_candidate"):
            reasons.append("possible_duplicate")
        if tx.get("merchant_identity_method") == "ambiguous_alias":
            reasons.append("ambiguous_merchant_match")
        if reasons:
            queue.append({
                "transaction_index": index,
                "transaction_id": tx.get("transaction_id"),
                "date": tx.get("transaction_date"),
                "merchant": tx.get("merchant"),
                "amount": float(tx.get("amount") or 0),
                "category": tx.get("main_category") or tx.get("category") or "Other",
                "confidence": confidence,
                "reasons": reasons,
                "priority": "high" if "possible_duplicate" in reasons or confidence < 0.4 else "normal",
            })
    return sorted(queue, key=lambda item: (item["priority"] != "high", item["confidence"]))
