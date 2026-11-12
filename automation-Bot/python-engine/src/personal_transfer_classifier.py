
"""Conservative P2P classification with per-user confirmed contact memory."""

from __future__ import annotations

import json
from pathlib import Path

from src.merchant_normalizer import normalize_text


ROOT = Path(__file__).resolve().parents[1]

RELATIONSHIP_PATH = ROOT / "data" / "relationship_aliases.json"
CONTACTS_PATH = ROOT / "data" / "personal_contacts.json"


INCOMING_PHRASES = [
    "received from",
    "payment from",
    "credited by",
    "received via upi",
    "upi from",
]

OUTGOING_PHRASES = [
    "paid to",
    "sent to",
    "transferred to",
    "payment to",
    "upi to",
]


def _read_json(path, default):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return default


def _has_phrase(text, phrase):
    text_n = f" {normalize_text(text)} "
    phrase_n = normalize_text(phrase)

    return bool(phrase_n and f" {phrase_n} " in text_n)


def _flow(text, direction):
    """Determine transfer direction from explicit wording or direction."""

    if any(
        _has_phrase(text, phrase)
        for phrase in INCOMING_PHRASES
    ):
        return "incoming"

    if any(
        _has_phrase(text, phrase)
        for phrase in OUTGOING_PHRASES
    ):
        return "outgoing"

    direction_value = str(direction or "").lower().strip()

    if direction_value in {"credit", "income"}:
        return "incoming"

    if direction_value in {"expense", "debit"}:
        return "outgoing"

    return None


def save_personal_contact(
    user_id,
    contact_name,
    relationship,
    aliases=None,
    path=None,
):
    """Save a contact only after explicit user confirmation."""

    if user_id is None:
        raise ValueError("user_id is required")

    if not isinstance(contact_name, str) or not contact_name.strip():
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
        "confirmed_by_user": True,
    }

    store_path.parent.mkdir(parents=True, exist_ok=True)

    temp = store_path.with_suffix(".tmp")

    temp.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    temp.replace(store_path)

    return data[str(user_id)]["contacts"][key]


def classify_personal_transfer(
    counterparty=None,
    description=None,
    direction=None,
    user_id=None,
    contacts_path=None,
    relationship_path=None,
):
    """
    Classify personal transfers conservatively.

    Confirmed contacts are automatically classified.
    Unknown counterparties are returned as reviewable P2P candidates
    only when explicit transfer wording is present.

    A person's name alone is never sufficient evidence.
    """

    text = " ".join(
        str(value)
        for value in (counterparty, description)
        if value
    )

    text_n = normalize_text(text)

    flow = _flow(text, direction)

    rel_data = _read_json(
        relationship_path or RELATIONSHIP_PATH,
        {},
    )

    contacts_data = _read_json(
        contacts_path or CONTACTS_PATH,
        {},
    )

    user_contacts = (
        contacts_data.get(str(user_id), {}).get("contacts", {})
        if user_id is not None
        else {}
    )

    # --------------------------------------------------
    # 1. Explicit self-transfer detection
    # --------------------------------------------------

    self_phrases = rel_data.get("self_transfer_phrases") or [
        "self transfer",
        "own account",
        "transfer to own account",
        "between my accounts",
    ]

    if any(
        _has_phrase(text_n, phrase)
        for phrase in self_phrases
    ):
        return {
            "category": "Personal Transfers",
            "main_category": "Personal Transfers",
            "subcategory": "Self Transfer",
            "transaction_subtype": "self_transfer",
            "classification_method": "explicit_self_transfer_phrase",
            "confidence": 0.99,
            "needs_review": False,
            "is_internal_transfer": True,
            "exclude_from_expense_total": True,
            "exclude_from_income_total": True,
            "transaction_type": "transfer",
        }

    # No transfer direction means no P2P classification.
    if flow is None:
        return None

    # --------------------------------------------------
    # 2. Confirmed contact memory (user-specific)
    # --------------------------------------------------

    cp = normalize_text(counterparty or "")

    for key, details in user_contacts.items():

        aliases = {
            normalize_text(key),
            normalize_text(details.get("display_name", "")),
        }

        aliases.update(
            normalize_text(alias)
            for alias in details.get("aliases", [])
        )

        aliases.discard("")

        if cp and cp in aliases:

            if not details.get("confirmed_by_user", False):
                continue

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
                "transaction_subtype": f"p2p_{flow}",
                "classification_method": "user_confirmed_contact",
                "confidence": 0.99,
                "needs_review": False,
                "counterparty_name": (
                    details.get("display_name") or counterparty
                ),
                "transaction_type": (
                    "credit" if flow == "incoming" else "expense"
                ),
                "exclude_from_income_total": flow == "incoming",
                "exclude_from_expense_total": False,
                "is_internal_transfer": False,
                "is_p2p": True,
            }

    # --------------------------------------------------
    # 3. Explicit relationship aliases
    # --------------------------------------------------

    for relationship_group in ("family", "friends"):

        group = rel_data.get(relationship_group, {})

        for _, aliases in group.items():

            if any(
                _has_phrase(text_n, alias)
                for alias in aliases
            ):

                return {
                    "category": "Personal Transfers",
                    "main_category": "Personal Transfers",
                    "subcategory": (
                        "Family"
                        if relationship_group == "family"
                        else "Friends"
                    ),
                    "transaction_subtype": f"p2p_{flow}",
                    "classification_method": "explicit_relationship_term",
                    "confidence": 0.90,
                    "needs_review": False,
                    "transaction_type": (
                        "credit" if flow == "incoming" else "expense"
                    ),
                    "exclude_from_income_total": flow == "incoming",
                    "exclude_from_expense_total": False,
                    "is_internal_transfer": False,
                    "is_p2p": True,
                }

    # --------------------------------------------------
    # 4. Unknown P2P candidate
    # --------------------------------------------------

    # Explicit transfer wording is required.
    # Do not classify a name without transfer evidence.

    return {
        "category": "Personal Transfers",
        "main_category": "Personal Transfers",
        "subcategory": "Person-to-Person",
        "transaction_subtype": f"p2p_{flow}",
        "classification_method": "unknown_person_transfer",
        "confidence": 0.65,
        "needs_review": True,
        "counterparty_name": counterparty,
        "transaction_type": (
            "credit" if flow == "incoming" else "expense"
        ),
        "exclude_from_income_total": flow == "incoming",
        "exclude_from_expense_total": False,
        "is_internal_transfer": False,
        "is_p2p": True,
    }
