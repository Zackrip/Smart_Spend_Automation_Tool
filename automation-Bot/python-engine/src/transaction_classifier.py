import re

# ==========================================
# 1. MERCHANT ALIASES
# ==========================================

MERCHANT_ALIASES = {
    "swiggy": "Food",
    "zomato": "Food",
    "dominos": "Food",
    "mcdonalds": "Food",
    "VADA PAV": "Food",

    "blinkit": "Groceries",
    "zepto": "Groceries",
    "bigbasket": "Groceries",

    "amazon": "Shopping",
    "flipkart": "Shopping",
    "myntra": "Shopping",
    "zudio": "Shopping",

    "uber": "Travel",
    "ola": "Travel",
    "rapido": "Travel",

    "netflix": "Entertainment",
    "spotify": "Entertainment",

    "apollo pharmacy": "Healthcare",
    "medplus": "Healthcare"
}


# ==========================================
# 2. CATEGORY KEYWORDS
# ==========================================

CATEGORY_KEYWORDS = {

    "Groceries": [
        "grocery",
        "groceries",
        "supermarket",
        "kirana",
        "vegetables",
        "fruits",
        "provision store"
    ],

    "Food": [
        "restaurant",
        "cafe",
        "food",
        "pizza",
        "bakery",
        "dhaba",
        "fast food",
        "food stall",
        "tea stall",
        "juice corner",
        "sweet shop"
    ],

    "Shopping": [
        "shopping",
        "clothing",
        "fashion",
        "electronics",
        "mobile shop",
        "footwear"
    ],

    "Travel": [
        "taxi",
        "cab",
        "metro",
        "railway",
        "irctc",
        "flight",
        "bus ticket",
        "petrol pump",
        "fuel station"
    ],

    "Bills": [
        "electricity bill",
        "water bill",
        "mobile recharge",
        "broadband",
        "gas bill",
        "internet bill"
    ],

    "Entertainment": [
        "movie",
        "cinema",
        "netflix",
        "spotify",
        "hotstar",
        "prime video"
    ],

    "Healthcare": [
        "hospital",
        "pharmacy",
        "medical store",
        "medicine",
        "clinic",
        "doctor"
    ],

    "Education": [
        "college",
        "school",
        "university",
        "tuition",
        "course fee",
        "education"
    ]
}


# ==========================================
# 3. TEXT MATCHING
# ==========================================

def contains_keyword(text, keyword):

    pattern = (
        r"(?<!\w)"
        + re.escape(keyword)
        + r"(?!\w)"
    )

    return bool(
        re.search(pattern, text, re.IGNORECASE)
    )


# ==========================================
# 4. MAIN CLASSIFIER
# ==========================================

def classify_transaction(
    counterparty=None,
    notification_text=None,
    user_category=None
):

    text = " ".join(
        value.strip()
        for value in [
            counterparty,
            notification_text
        ]
        if isinstance(value, str) and value.strip()
    ).lower()

    # User-confirmed category takes priority.
    if user_category:
        return {
            "category": user_category,
            "classification_method": "user_confirmed",
            "needs_review": False
        }

    if not text:

        return {
            "category": "Other",
            "classification_method": "unknown",
            "needs_review": True
        }

    # Match known merchant aliases.
    for merchant, category in MERCHANT_ALIASES.items():

        if contains_keyword(text, merchant):

            return {
                "category": category,
                "classification_method": "merchant_alias",
                "needs_review": False
            }

    # Match recognizable category keywords.
    for category, keywords in CATEGORY_KEYWORDS.items():

        for keyword in keywords:

            if contains_keyword(text, keyword):

                return {
                    "category": category,
                    "classification_method": "keyword",
                    "needs_review": False
                }

    # Unknown person or merchant.
    return {
        "category": "Other",
        "classification_method": "unknown",
        "needs_review": True
    }
