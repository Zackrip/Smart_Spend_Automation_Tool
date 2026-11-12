"""Conservative counterparty-type detection.

A name is only a P2P candidate when transfer wording is also present.
This module never decides family/friend relationship.
"""
import re
from src.merchant_normalizer import normalize_text

BUSINESS_TERMS = {
    "store", "shop", "mart", "restaurant", "hotel", "cafe", "services",
    "service", "solutions", "enterprise", "enterprises", "foods", "food",
    "pharmacy", "medical", "traders", "trading", "company", "pvt",
    "limited", "ltd", "llp", "bank", "telecom", "mobility", "supermarket",
    "bhandar", "kirana", "dhaba", "bakery", "chemist", "clinic", "hospital",
    "agency", "departmental", "provision", "dairy", "petrol", "filling",
    "stationery", "garments", "jewellers", "electronics"
}

TRANSFER_PATTERNS = [
    (r"\bpaid\s+to\s+(.+?)(?=\s+(?:using|via|through|from|by)\b|[.,;]|$)", "outgoing"),
    (r"\bsent\s+to\s+(.+?)(?=\s+(?:using|via|through|from|by)\b|[.,;]|$)", "outgoing"),
    (r"\bpayment\s+to\s+(.+?)(?=\s+(?:using|via|through|from|by)\b|[.,;]|$)", "outgoing"),
    (r"\btransferred\s+to\s+(.+?)(?=\s+(?:using|via|through|from|by)\b|[.,;]|$)", "outgoing"),
    (r"\breceived\s+from\s+(.+?)(?=\s+(?:using|via|through|from|by)\b|[.,;]|$)", "incoming"),
    (r"\bpayment\s+from\s+(.+?)(?=\s+(?:using|via|through|from|by)\b|[.,;]|$)", "incoming"),
    (r"\bcredited\s+by\s+(.+?)(?=\s+(?:using|via|through|from|by)\b|[.,;]|$)", "incoming"),
]

def _clean_candidate(value):
    value = re.sub(r"\s+", " ", str(value or "")).strip(" .,:;-")
    value = re.sub(r"\s+(?:upi|imps|neft|rtgs)\s*(?:payment|transfer)?$", "", value, flags=re.I)
    return value.strip()

def _looks_like_person(value):
    candidate = _clean_candidate(value)
    words = candidate.split()
    if not 2 <= len(words) <= 4:
        return False
    if any(word.lower().rstrip(".") in BUSINESS_TERMS for word in words):
        return False
    # Supports common Indian names with initials and hyphens.
    return all(
        re.fullmatch(r"[A-Za-z][A-Za-z'.-]*", word)
        for word in words
    )

def detect_counterparty(counterparty=None, description=None):
    raw_counterparty = _clean_candidate(counterparty)
    text = " ".join(x for x in (str(description or ""), str(counterparty or "")) if x)
    transfer_direction = None
    extracted_name = None

    for pattern, flow in TRANSFER_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            transfer_direction = flow
            extracted_name = _clean_candidate(match.group(1))
            break

    candidate = raw_counterparty
    if candidate.lower() in {"", "unknown", "upi", "not available", "na"}:
        candidate = extracted_name or ""

    if not candidate and extracted_name:
        candidate = extracted_name

    # A known merchant classifier should run before using this P2P candidate.
    is_person = bool(
        transfer_direction
        and candidate
        and _looks_like_person(candidate)
    )

    return {
        "counterparty_name": candidate or None,
        "is_person_candidate": is_person,
        "transfer_direction": transfer_direction,
        "confidence": 0.72 if is_person else 0.0
    }
