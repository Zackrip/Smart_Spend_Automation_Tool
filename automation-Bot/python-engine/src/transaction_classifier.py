
import json
from pathlib import Path

from src.merchant_normalizer import normalize_text
from src.merchant_learning import get_user_mapping


# ==========================================
# 1. FILE PATHS
# ==========================================

DATA = Path(__file__).resolve().parents[1] / "data"

MAPPINGS_PATH = DATA / "user_merchant_mappings.json"
KNOWLEDGE_PATH = DATA / "merchant_knowledge.json"


# ==========================================
# 2. LOAD JSON DATA SAFELY
# ==========================================

def _load(path, default=None):
    if default is None:
        default = {}

    try:
        with Path(path).open("r", encoding="utf-8") as file:
            return json.load(file)

    except (FileNotFoundError, json.JSONDecodeError):
        return default


# ==========================================
# 3. TEXT MATCHING
# ==========================================

def _match(text, rules):

    text_n = normalize_text(text)

    if not text_n or not isinstance(rules, dict):
        return None

    found = []

    for category, terms in rules.items():

        if not isinstance(terms, dict):
            continue

        for term, subcategory in terms.items():

            term_n = normalize_text(term)

            if not term_n:
                continue

            # Exact phrase / word-boundary matching
            if f" {term_n} " in f" {text_n} ":

                found.append({
                    "length": len(term_n),
                    "main_category": category,
                    "subcategory": subcategory,
                    "term": term
                })

    if not found:
        return None

    # Longest matching phrase gets priority.
    longest_length = max(item["length"] for item in found)

    best_matches = [
        item for item in found
        if item["length"] == longest_length
    ]

    # Same-strength matches across different categories
    # should not be guessed.
    categories = {
        item["main_category"]
        for item in best_matches
    }

    if len(categories) > 1:
        return {"ambiguous": True}

    return best_matches[0]


# ==========================================
# 4. MAIN CLASSIFIER
# ==========================================

def classify_transaction(
    counterparty=None,
    notification_text=None,
    user_category=None,
    user_subcategory=None,
    user_id=None,
    transaction_type=None,
    transaction_description=None,
    knowledge_path=KNOWLEDGE_PATH
):

    knowledge = _load(knowledge_path, {
        "merchant_aliases": {},
        "business_keywords": {}
    })

    merchant = counterparty or ""

    combined = " ".join(
        value.strip()
        for value in (
            merchant,
            transaction_description,
            notification_text
        )
        if isinstance(value, str) and value.strip()
    )

    # --------------------------------------
    # PRIORITY 1: USER-CONFIRMED CATEGORY
    # --------------------------------------

    if user_category:

        return {
            "category": user_category,
            "main_category": user_category,
            "subcategory": user_subcategory or "Unspecified",
            "classification_method": "user_confirmed",
            "confidence": 1.0,
            "needs_review": False
        }

    # --------------------------------------
    # PRIORITY 2: PERSONAL MERCHANT MEMORY
    # --------------------------------------

    if user_id is not None and merchant:

        personal = get_user_mapping(
            user_id=user_id,
            merchant=merchant,
            path=MAPPINGS_PATH
        )

        if personal:

            main = personal.get("main_category", "Other")
            sub = personal.get("subcategory", "Uncategorised")

            return {
                "category": main,
                "main_category": main,
                "subcategory": sub,
                "classification_method": "personal_merchant_memory",
                "confidence": 1.0,
                "needs_review": False
            }

    # --------------------------------------
    # PRIORITY 3: GLOBAL MERCHANT ALIASES
    # --------------------------------------

    aliases = knowledge.get("merchant_aliases", {})

    match = _match(merchant, aliases)

    method = "global_merchant_alias"

    # --------------------------------------
    # PRIORITY 4: BUSINESS KEYWORDS
    # --------------------------------------

    if not match:

        match = _match(
            combined,
            knowledge.get("business_keywords", {})
        )

        method = "business_keyword"

    # --------------------------------------
    # PRIORITY 5: HANDLE MATCH RESULT
    # --------------------------------------

    if match and match.get("ambiguous"):

        return {
            "category": "Other",
            "main_category": "Other",
            "subcategory": "Uncategorised",
            "classification_method": "ambiguous_match",
            "confidence": 0.0,
            "needs_review": True
        }

    if match:

        main = match["main_category"]
        sub = match["subcategory"]

        return {
            "category": main,
            "main_category": main,
            "subcategory": sub,
            "classification_method": method,
            "confidence": 0.93,
            "needs_review": False
        }

    # --------------------------------------
    # PRIORITY 6: UNKNOWN TRANSACTION
    # --------------------------------------

    return {
        "category": "Other",
        "main_category": "Other",
        "subcategory": "Uncategorised",
        "classification_method": "unknown",
        "confidence": 0.0,
        "needs_review": True
    }
