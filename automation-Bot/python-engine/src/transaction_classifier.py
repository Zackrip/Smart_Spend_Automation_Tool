
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
# 2. LOAD JSON DATA
# ==========================================

def _load(path):
    with Path(path).open(encoding="utf-8") as file:
        return json.load(file)


# ==========================================
# 3. MATCH MERCHANT / BUSINESS KEYWORDS
# ==========================================

def _match(text, rules):

    text_n = normalize_text(text)
    found = []

    for category, terms in rules.items():

        for term, subcategory in terms.items():

            term_n = normalize_text(term)

            if term_n and f" {term_n} " in f" {text_n} ":

                found.append(
                    (
                        len(term_n),
                        category,
                        subcategory,
                        term
                    )
                )

    if not found:
        return None

    found.sort(reverse=True)

    best = found[0]

    tied = [
        item for item in found
        if item[0] == best[0]
    ]

    # Check whether equally strong matches conflict.
    if len({item[1] for item in tied}) > 1:
        return {"ambiguous": True}

    return {
        "main_category": best[1],
        "subcategory": best[2],
        "term": best[3]
    }


# ==========================================
# 4. MAIN TRANSACTION CLASSIFIER
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

    # Load global merchant knowledge.
    knowledge = _load(knowledge_path)

    merchant = counterparty or ""

    combined = " ".join(
        value
        for value in (
            merchant,
            transaction_description,
            notification_text
        )
        if isinstance(value, str)
    )

    # --------------------------------------
    # PRIORITY 1: USER CONFIRMED CATEGORY
    # --------------------------------------

    if user_category:

        main = user_category
        sub = user_subcategory or "Unspecified"

        method = "user_confirmed"
        confidence = 1.0
        review = False

    else:

        # --------------------------------------
        # PRIORITY 2: PERSONAL MERCHANT MEMORY
        # --------------------------------------

        personal = None

        if user_id is not None and merchant:

            personal = get_user_mapping(
                user_id=user_id,
                merchant=merchant,
                path=MAPPINGS_PATH
            )

        if personal:

            main = personal["main_category"]
            sub = personal["subcategory"]

            method = "personal_merchant_memory"
            confidence = 1.0
            review = False

        else:

            # --------------------------------------
            # PRIORITY 3: GLOBAL MERCHANT ALIASES
            # --------------------------------------

            aliases = {
                category: {
                    alias: subcategory
                    for alias, subcategory in values.items()
                }
                for category, values
                in knowledge.get("merchant_aliases", {}).items()
            }

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
            # PRIORITY 5: FINAL CLASSIFICATION
            # --------------------------------------

            if match and match.get("ambiguous"):

                main = "Other"
                sub = "Uncategorised"

                confidence = 0.0
                review = True

                method = "ambiguous_match"

            elif match:

                main = match["main_category"]
                sub = match["subcategory"]

                confidence = 0.93
                review = False

            else:

                main = "Other"
                sub = "Uncategorised"

                confidence = 0.0
                review = True

                method = "unknown"

    # --------------------------------------
    # 6. RETURN CLASSIFICATION
    # --------------------------------------

    return {
        "category": main,
        "main_category": main,
        "subcategory": sub,
        "classification_method": method,
        "confidence": confidence,
        "needs_review": review
    }
