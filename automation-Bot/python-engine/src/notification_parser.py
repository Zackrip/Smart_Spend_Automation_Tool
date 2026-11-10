import re
from datetime import datetime


# ==========================================
# 1. AMOUNT EXTRACTION
# ==========================================

def extract_amount(text):
    patterns = [
        r"(?:₹|rs\.?|inr)\s*([\d,]+(?:\.\d{1,2})?)",
        r"([\d,]+(?:\.\d{1,2})?)\s*(?:rupees|inr)"
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            return float(match.group(1).replace(",", ""))

    return None


# ==========================================
# 2. TRANSACTION TYPE
# ==========================================

def extract_transaction_type(text):
    text = text.lower()

    failed = [
        "payment failed",
        "transaction failed",
        "payment unsuccessful",
        "has failed",
        "failed",
        "declined"
    ]

    refund = [
        "refund",
        "reversed",
        "reversal",
        "cashback received"
    ]

    income = [
        "credited",
        "received",
        "deposited",
        "salary credited"
    ]

    expense = [
        "debited",
        "paid",
        "spent",
        "sent",
        "withdrawn",
        "purchase successful",
        "pos transaction",
        "atm withdrawal"
    ]

    if any(word in text for word in failed):
        return "failed"

    if any(word in text for word in refund):
        return "refund"

    if any(word in text for word in income):
        return "income"

    if any(word in text for word in expense):
        return "expense"

    return "unknown"


# ==========================================
# 3. PAYMENT STATUS
# ==========================================

def extract_payment_status(text):
    text = text.lower()

    if any(word in text for word in [
        "payment failed",
        "transaction failed",
        "declined",
        "unsuccessful"
    ]):
        return "failed"

    if any(word in text for word in [
        "payment confirmed",
        "successfully paid",
        "payment successful",
        "transaction successful"
    ]):
        return "successful"

    if "refund" in text or "reversed" in text:
        return "refunded"

    return "unknown"


# ==========================================
# 4. MERCHANT / COUNTERPARTY
# ==========================================

def extract_counterparty(text, sender=None):

    patterns = [
        # Example: Your Swiggy Order #123
        r"\byour\s+([a-zA-Z][a-zA-Z0-9 &'.-]{1,50}?)\s+order\s*#",

        # Example: Paid Rs. 450 to Rahul Sharma
        r"\b(?:paid|sent|transferred)\s+(?:rs\.?|inr|₹)?\s*[\d,]+(?:\.\d{1,2})?\s+to\s+(.+?)(?=\s+(?:via|using|through|on|ref|txn|upi)\b|[.,;]|$)",

        # Example: Received from Amit Kumar
        r"\b(?:received|credited)\s+from\s+(.+?)(?=\s+(?:via|using|through|on|ref|txn|upi)\b|[.,;]|$)",

        # Example: Payment at XYZ Store
        r"\b(?:at|merchant\s*[:=-])\s+([A-Za-z][A-Za-z0-9 &'.-]{1,50})(?=\s+(?:on|via|using|card|pos|ref|txn)\b|[.,;]|$)"
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            return match.group(1).strip(" .,:;-")[:100]

    # Use sender only as a fallback.
    # AD-SWIGGY-S becomes SWIGGY.
    if sender:
        cleaned_sender = re.sub(
            r"[^A-Za-z0-9 ]",
            " ",
            sender
        )

        sender_words = cleaned_sender.split()

        if sender_words:
            return sender_words[-1].upper()

    return None


# ==========================================
# 5. ORDER ID
# ==========================================

def extract_order_id(text):

    pattern = (
        r"\border\s*#\s*([A-Z0-9-]+)"
    )

    match = re.search(
        pattern,
        text,
        re.IGNORECASE
    )

    return match.group(1) if match else None


# ==========================================
# 6. TRANSACTION REFERENCE
# ==========================================

def extract_reference(text):

    patterns = [
        r"\b(?:txn|transaction)\s*id\s*[:#=-]?\s*([A-Z0-9]+)",
        r"\b(?:upi\s*ref(?:erence)?|utr|rrn|ref(?:erence)?\s*(?:no|number|id)?)\s*[:#=-]?\s*([A-Z0-9]+)"
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:
            return match.group(1).upper()

    return None


# ==========================================
# 7. DATE EXTRACTION
# ==========================================

def extract_transaction_date(text):

    patterns = [
        r"\b(\d{2}/\d{2}/\d{4})\b",
        r"\b(\d{2}-\d{2}-\d{4})\b",
        r"\b(\d{4}-\d{2}-\d{2})\b"
    ]

    for pattern in patterns:
        match = re.search(pattern, text)

        if match:
            value = match.group(1)

            formats = [
                "%d/%m/%Y",
                "%d-%m-%Y",
                "%Y-%m-%d"
            ]

            for fmt in formats:
                try:
                    return datetime.strptime(
                        value, fmt
                    ).date().isoformat()
                except ValueError:
                    continue

    return None


# ==========================================
# 8. TIME EXTRACTION
# ==========================================

def extract_transaction_time(text):

    pattern = (
        r"\b(\d{1,2}:\d{2}\s*(?:AM|PM))\b"
    )

    match = re.search(
        pattern,
        text,
        re.IGNORECASE
    )

    if match:
        value = match.group(1).upper()

        try:
            parsed = datetime.strptime(
                value, "%I:%M %p"
            )

            return parsed.strftime("%H:%M:%S")

        except ValueError:
            return None

    return None


# ==========================================
# 9. PAYMENT METHOD
# ==========================================

def extract_payment_method(text):

    text = text.lower()

    if any(word in text for word in [
        "upi", "gpay", "google pay",
        "phonepe", "paytm", "bhim"
    ]):
        return "UPI"

    if "credit card" in text:
        return "Credit Card"

    if "debit card" in text:
        return "Debit Card"

    if any(word in text for word in [
        "neft", "imps", "rtgs"
    ]):
        return "Bank Transfer"

    if "pos" in text or "point of sale" in text:
        return "Card/POS"

    if "atm" in text or "cash withdrawal" in text:
        return "ATM"

    if "net banking" in text:
        return "Net Banking"

    return "Unknown"


# ==========================================
# 10. MAIN EXTRACTION FUNCTION
# ==========================================

def extract_transaction(notification, sender=None):

    if not isinstance(notification, str):
        raise ValueError("Notification must be text.")

    if not notification.strip():
        raise ValueError("Notification cannot be empty.")

    amount = extract_amount(notification)

    transaction_type = extract_transaction_type(
        notification
    )

    payment_status = extract_payment_status(
        notification
    )

    counterparty = extract_counterparty(
        notification,
        sender
    )

    return {
        "amount": amount,
        "counterparty": counterparty,
        "transaction_type": transaction_type,
        "payment_status": payment_status,
        "payment_method": extract_payment_method(notification),
        "order_id": extract_order_id(notification),
        "transaction_reference": extract_reference(notification),
        "transaction_date": extract_transaction_date(notification),
        "transaction_time": extract_transaction_time(notification),
        "needs_review": (
            amount is None
            or transaction_type == "unknown"
            or payment_status == "unknown"
            or counterparty is None
        )
    }
