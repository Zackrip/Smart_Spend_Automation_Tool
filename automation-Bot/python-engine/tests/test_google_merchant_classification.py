from src.transaction_classifier import classify_transaction


def test_google_one_is_cloud_storage():
    result = classify_transaction(
        counterparty="Google One",
        transaction_description="Google One subscription"
    )
    assert result["main_category"] == "Subscriptions"
    assert result["subcategory"] == "Cloud Storage"
    assert result["needs_review"] is False


def test_google_drive_storage_is_cloud_storage():
    result = classify_transaction(
        counterparty="Google",
        transaction_description="Google Drive storage payment"
    )
    assert result["main_category"] == "Subscriptions"
    assert result["subcategory"] == "Cloud Storage"


def test_google_workspace_is_productivity_subscription():
    result = classify_transaction(
        counterparty="Google Workspace"
    )
    assert result["main_category"] == "Subscriptions"
    assert result["subcategory"] == "Software & Productivity"


def test_google_play_recharge_remains_mobile_recharge():
    result = classify_transaction(
        counterparty="Google Play",
        transaction_description="Recharge code purchased Google Play"
    )
    assert result["main_category"] == "Bills"
    assert result["subcategory"] == "Mobile Recharge"


def test_generic_google_payment_is_not_assumed_to_be_cloud_storage():
    result = classify_transaction(
        counterparty="Google",
        transaction_description="Payment to Google"
    )
    assert result["main_category"] == "Other"
    assert result["subcategory"] == "Uncategorised"
    assert result["needs_review"] is True
