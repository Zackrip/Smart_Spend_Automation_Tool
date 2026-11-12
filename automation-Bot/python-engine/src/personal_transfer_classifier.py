
import json
from pathlib import Path

from src.merchant_normalizer import normalize_text


# ==========================================
# 1. FILE PATHS
# ==========================================

ROOT = Path(__file__).resolve().parents[1]

RELATIONSHIP_PATH = ROOT / "data" / "relationship_aliases.json"
CONTACTS_PATH = ROOT / "data" / "personal_contacts.json"


# ==========================================
# 2. JSON HELPER
# ==========================================

def _read_json(path, default=None):

    if default is None:
        default = {}

    try:
        return json.loads(
            Path(path).read_text(encoding="utf-8")
        )

    except (FileNotFoundError, json.JSONDecodeError):
        return default


# ==========================================
# 3. TEXT MATCHING
# ==========================================

def _contains_phrase(text, phrase):

    text_n = normalize_text(text)
    phrase_n = normalize_text(phrase)

    if not text_n or not phrase_n:
        return False

    return f" {phrase_n} " in f" {text_n} "


def _is_incoming(direction):

    return (direction or "").lower() in {
        "credit",
        "incoming",
        "received"
    }


# ==========================================
# 4. SAVE USER-CONFIRMED CONTACT
# ==========================================

def save_personal_contact(
    user_id,
    contact_name,
    relationship,
    aliases=None,
    path=None
):

    if user_id is None:
        raise ValueError("user_id is required")

    if not contact_name or not contact_name.strip():
        raise ValueError("contact_name is required")

    if relationship not in {"family", "friends", "other"}:
        raise ValueError(
            "relationship must be family, friends, or other"
        )

    store_path = Path(path) if path else CONTACTS_PATH

    data = _read_json(store_path, {})

    key = normalize_text(contact_name)

    data.setdefault(str(user_id), {}).setdefault(
        "contacts", {}
    )[key] = {
        "display_name": contact_name.strip(),
        "relationship": relationship,
        "aliases": sorted({
            normalize_text(alias)
            for alias in (aliases or [])
            if isinstance(alias, str) and normalize_text(alias)
        }),
        "confirmed_by_user": True
    }

    store_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    store_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    return data[str(user_id)]["contacts"][key]


# ==========================================
# 5. PERSONAL TRANSFER CLASSIFIER
# ==========================================

def classify_personal_transfer(
    counterparty=None,
    description=None,
    direction=None,
    user_id=None,
    contacts_path=None,
    relationship_path=None
):

    """
    Classifies personal transfers only when there is
    stronger evidence than a generic 'paid to' phrase.

    Accepted evidence:
    1. Explicit self-transfer wording.
    2. Exact match with a user-confirmed contact.
    3. Explicit relationship alias with transfer wording.

    Unknown recipients remain Other / Needs Review.
    """

    text = " ".join(
        value
        for value in (counterparty, description)
        if isinstance(value, str)
    )

    text_n = normalize_text(text)
    counterparty_n = normalize_text(counterparty)

    if not text_n:
        return None

    rel_data = _read_json(
        relationship_path or RELATIONSHIP_PATH,
        {}
    )

    contacts_data = _read_json(
        contacts_path or CONTACTS_PATH,
        {}
    )

    user_contacts = (
        contacts_data.get(str(user_id), {}).get("contacts", {})
        if user_id is not None
        else {}
    )

    # --------------------------------------
    # PRIORITY 1: EXPLICIT SELF TRANSFER
    # --------------------------------------

    self_phrases = [
        "self transfer",
        "own account",
        "transfer to own account",
        "between my accounts"
    ]

    if any(
        _contains_phrase(text_n, phrase)
        for phrase in self_phrases
    ):

        return {
            "category": "Personal Transfers",
            "main_category": "Personal Transfers",
            "subcategory": "Self Transfer",
            "transaction_subtype": "self_transfer",
            "classification_method": "explicit_self_transfer_phrase",
            "confidence": 0.98,
            "needs_review": False
        }

    # --------------------------------------
    # PRIORITY 2: TRANSFER LANGUAGE
    # --------------------------------------

    transfer_phrases = rel_data.get(
        "transfer_phrases",
        [
            "paid to",
            "payment to",
            "upi payment to",
            "sent to",
            "transferred to",
            "received from",
            "payment from",
            "credited by",
            "upi to",
            "upi from",
            "upi transfer"
        ]
    )

    has_transfer_language = any(
        _contains_phrase(text_n, phrase)
        for phrase in transfer_phrases
    )

    if not has_transfer_language:
        return None

    # --------------------------------------
    # PRIORITY 3: USER-CONFIRMED CONTACT
    # --------------------------------------

    for key, details in user_contacts.items():

        if not details.get("confirmed_by_user", False):
            continue

        candidates = {
            normalize_text(key),
            normalize_text(details.get("display_name", ""))
        }

        candidates.update(
            normalize_text(alias)
            for alias in details.get("aliases", [])
        )

        candidates.discard("")

        # Match the actual counterparty, not the entire narration.
        if counterparty_n in candidates:

            relationship = details.get("relationship")

            if relationship == "family":
                subcategory = "Family"

            elif relationship == "friends":
                subcategory = "Friends"

            else:
                subcategory = "Other Personal"

            return {
                "category": "Personal Transfers",
                "main_category": "Personal Transfers",
                "subcategory": subcategory,
                "transaction_subtype": (
                    "p2p_incoming"
                    if _is_incoming(direction)
                    else "p2p_outgoing"
                ),
                "classification_method": "user_confirmed_contact",
                "confidence": 0.98,
                "needs_review": False
            }

    # --------------------------------------
    # PRIORITY 4: EXPLICIT RELATIONSHIP ALIAS
    # --------------------------------------

    for relationship in ("family", "friends"):

        relationship_data = rel_data.get(
            relationship, {}
        )

        for aliases in relationship_data.values():

            for alias in aliases:

                if _contains_phrase(text_n, alias):

                    subcategory = (
                        "Family"
                        if relationship == "family"
                        else "Friends"
                    )

                    return {
                        "category": "Personal Transfers",
                        "main_category": "Personal Transfers",
                        "subcategory": subcategory,
                        "transaction_subtype": (
                            "p2p_incoming"
                            if _is_incoming(direction)
                            else "p2p_outgoing"
                        ),
                        "classification_method": "explicit_relationship_term",
                        "confidence": 0.88,
                        "needs_review": False
                    }

    # --------------------------------------
    # PRIORITY 5: UNKNOWN RECIPIENT
    # --------------------------------------

    # A generic 'paid to' or 'payment to' phrase does not
    # prove that the recipient is a person.
    # Let the main classifier keep it as Other / Review.

    return None
