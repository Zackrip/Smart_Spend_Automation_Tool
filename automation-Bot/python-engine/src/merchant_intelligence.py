"""Merchant identity enrichment built on Paisora's existing knowledge base.

This module adds normalized identity/match metadata. Category decisions remain
owned by transaction_classifier.py, so this module cannot silently recategorize.
"""
import json
from pathlib import Path
from src.merchant_normalizer import normalize_text

KNOWLEDGE_PATH = Path(__file__).resolve().parents[1] / "data" / "merchant_knowledge.json"


def _load_knowledge(path=None):
    try:
        return json.loads(Path(path or KNOWLEDGE_PATH).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def identify_merchant(merchant, knowledge_path=None):
    display = str(merchant or "").strip()
    normalized = normalize_text(display)
    result = {
        "merchant_normalized": normalized or None,
        "merchant_match_term": None,
        "merchant_match_category": None,
        "merchant_match_subcategory": None,
        "merchant_identity_method": "normalized_only" if normalized else "missing",
    }
    if not normalized:
        return result
    aliases = _load_knowledge(knowledge_path).get("merchant_aliases", {})
    matches = []
    padded = f" {normalized} "
    for category, terms in aliases.items():
        if not isinstance(terms, dict):
            continue
        for term, subcategory in terms.items():
            term_n = normalize_text(term)
            if term_n and f" {term_n} " in padded:
                matches.append((len(term_n), category, term, subcategory))
    if matches:
        matches.sort(reverse=True)
        best_len = matches[0][0]
        best = [m for m in matches if m[0] == best_len]
        if len({m[1] for m in best}) == 1:
            _, category, term, subcategory = best[0]
            result.update({
                "merchant_match_term": term,
                "merchant_match_category": category,
                "merchant_match_subcategory": subcategory,
                "merchant_identity_method": "knowledge_alias",
            })
        else:
            result["merchant_identity_method"] = "ambiguous_alias"
    return result


def annotate_merchant_identity(transactions, knowledge_path=None):
    for tx in transactions:
        tx.update(identify_merchant(tx.get("merchant"), knowledge_path))
    return transactions
