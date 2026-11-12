
from src.personal_transfer_classifier import (
    classify_personal_transfer,
    save_personal_contact
)


def test_family_relationship():
    result = classify_personal_transfer(
        counterparty="Mummy",
        description="UPI payment to Mummy",
        direction="debit"
    )

    assert result["main_category"] == "Personal Transfers"
    assert result["subcategory"] == "Family"
    assert result["needs_review"] is False


def test_friends_relationship():
    result = classify_personal_transfer(
        counterparty="Dost",
        description="UPI payment to Dost",
        direction="debit"
    )

    assert result["subcategory"] == "Friends"


def test_unknown_person_requires_review():
    result = classify_personal_transfer(
        counterparty="Rahul Sharma",
        description="UPI paid to Rahul Sharma",
        direction="debit"
    )

    assert result["subcategory"] == "Person-to-Person"
    assert result["needs_review"] is True


def test_person_name_alone_is_not_transfer():
    result = classify_personal_transfer(
        counterparty="Rahul Sharma"
    )

    assert result is None


def test_user_contact_memory_is_private(tmp_path):
    contacts_file = tmp_path / "personal_contacts.json"

    save_personal_contact(
        user_id=101,
        contact_name="Rahul Sharma",
        relationship="friends",
        aliases=["Rahul"],
        path=contacts_file
    )

    user_one = classify_personal_transfer(
        counterparty="Rahul Sharma",
        description="UPI payment to Rahul Sharma",
        direction="debit",
        user_id=101,
        contacts_path=contacts_file
    )

    user_two = classify_personal_transfer(
        counterparty="Rahul Sharma",
        description="UPI payment to Rahul Sharma",
        direction="debit",
        user_id=202,
        contacts_path=contacts_file
    )

    assert user_one["subcategory"] == "Friends"
    assert user_two["subcategory"] == "Person-to-Person"
    assert user_two["needs_review"] is True
def test_debit_direction_alone_does_not_make_personal_transfer():

    result = classify_personal_transfer(
        counterparty="Google",
        description="Google",
        direction="debit"
    )

    assert result is None