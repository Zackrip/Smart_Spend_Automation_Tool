from src.transaction_classifier import classify_transaction
from src.transaction_type_detector import detect_transaction_type
from src.merchant_learning import save_user_mapping, get_user_mapping
def test_stationery():
    r=classify_transaction(counterparty="Sharma Stationers")
    assert (r["main_category"],r["subcategory"])==("Education","Stationery")
    assert not r["needs_review"]
def test_departmental_store():
    r=classify_transaction(counterparty="Gupta Departmental Store")
    assert (r["main_category"],r["subcategory"])==("Groceries","Departmental Store")
def test_jiohotstar():
    r=classify_transaction(counterparty="JioHotstar")
    assert (r["main_category"],r["subcategory"])==("Entertainment","OTT Subscription")
def test_person_name_review():
    assert classify_transaction(counterparty="Rahul Sharma")["needs_review"]
def test_cashback():
    assert detect_transaction_type("Cashback from PhonePe ₹1","credit")=={"transaction_type":"credit","transaction_subtype":"cashback"}
def test_wallet_topup():
    assert detect_transaction_type("Top-up Wallet","debit")=={"transaction_type":"transfer","transaction_subtype":"wallet_topup"}
def test_user_scoped_memory(tmp_path):
    p=tmp_path/"map.json"; save_user_mapping(101,"Mohit Kumar","Food","Street Food",p)
    assert get_user_mapping(101,"Mohit Kumar",p)["subcategory"]=="Street Food"
    assert get_user_mapping(202,"Mohit Kumar",p) is None
