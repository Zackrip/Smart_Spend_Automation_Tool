from src.transaction_classifier import classify_transaction
from src.merchant_learning import record_user_feedback
from src.statement_pdf_report import generate_statement_pdf

def test_known_merchant():
    result = classify_transaction(counterparty="Zudio Malviya Nagar")
    assert result["category"] == "Shopping"
    assert result["needs_review"] is False

def test_unknown_person_is_reviewed():
    result = classify_transaction(counterparty="Rahul Sharma")
    assert result["category"] == "Other"
    assert result["needs_review"] is True

def test_user_mapping_is_private_to_user(tmp_path, monkeypatch):
    import src.merchant_learning as learning
    import src.transaction_classifier as classifier
    mapping_file = tmp_path / "user_merchant_mappings.json"
    feedback_file = tmp_path / "feedback.csv"
    mapping_file.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(learning, "MAPPINGS_PATH", mapping_file)
    monkeypatch.setattr(learning, "FEEDBACK_PATH", feedback_file)
    monkeypatch.setattr(classifier, "MAPPINGS_PATH", mapping_file)
    saved = learning.record_user_feedback(101, "Rahul Sharma", "Food", "Other")
    assert saved["saved_category"] == "Food"
    assert classifier.classify_transaction(counterparty="Rahul Sharma", user_id=101)["category"] == "Food"
    assert classifier.classify_transaction(counterparty="Rahul Sharma", user_id=202)["category"] == "Other"

def test_pdf_returns_valid_pdf_bytes():
    transactions = [
        {"date": "2026-11-01", "merchant": "Zudio", "amount": 499, "type": "debit",
         "category": "Shopping", "needs_review": False},
        {"date": "2026-11-02", "merchant": "Rahul Sharma", "amount": 200, "type": "credit",
         "category": "Other", "needs_review": True}
    ]
    pdf = generate_statement_pdf(transactions)
    data = pdf.getvalue()
    assert data.startswith(b"%PDF")
    assert len(data) > 1000
