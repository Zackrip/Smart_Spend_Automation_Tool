import json
from pathlib import Path
from src.merchant_normalizer import normalize_text
FEEDBACK_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "feedback.csv"
)

MAPPINGS_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "user_merchant_mappings.json"
)


def _load(path=None):
    if path is None:
        path = MAPPINGS_PATH

    path = Path(path)

    if not path.exists():
        return {}

    try:
        return json.loads(path.read_text(encoding="utf-8"))

    except (json.JSONDecodeError, OSError) as exc:
        raise RuntimeError(
            f"Cannot read mapping store: {path}"
        ) from exc


def get_user_mapping(user_id, merchant, path=None):
    if user_id is None or not merchant:
        return None

    return _load(path).get(
        str(user_id), {}
    ).get(normalize_text(merchant))


def save_user_mapping(
    user_id,
    merchant,
    main_category,
    subcategory,
    path=None
):
    if user_id is None:
        raise ValueError("user_id is required")

    if not merchant or not merchant.strip():
        raise ValueError("merchant is required")

    if not main_category or not subcategory:
        raise ValueError(
            "main_category and subcategory are required"
        )

    if path is None:
        path = MAPPINGS_PATH

    path = Path(path)
    data = _load(path)

    data.setdefault(str(user_id), {})[
        normalize_text(merchant)
    ] = {
        "merchant_original": merchant.strip(),
        "main_category": main_category,
        "subcategory": subcategory,
        "confirmed": True
    }

    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    return data[str(user_id)][normalize_text(merchant)]


def record_user_feedback(
    user_id,
    merchant,
    category,
    subcategory,
    path=None
):
    saved = save_user_mapping(
        user_id=user_id,
        merchant=merchant,
        main_category=category,
        subcategory=subcategory,
        path=path
    )

    # Preserve the response format expected by the existing API and tests.
    return {
        "status": "success",
        "saved_category": saved["main_category"],
        "saved_subcategory": saved["subcategory"],
        "merchant": saved["merchant_original"],
        "user_id": user_id
    }