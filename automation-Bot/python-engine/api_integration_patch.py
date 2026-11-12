# 1) Keep the existing imports and add:
from src.merchant_learning import record_user_feedback

# 2) Add user_id to your existing NotificationRequest model:
# user_id: Optional[int] = None

# 3) In the existing /parse/notification endpoint, add user_id to the
# existing classify_transaction call (do not create a duplicate endpoint):
# classification = classify_transaction(
#     counterparty=result["counterparty"],
#     notification_text=request.notification_text,
#     user_category=request.user_category,
#     user_id=request.user_id
# )

# 4) Add this request model and endpoint once:
class CategoryFeedbackRequest(BaseModel):
    user_id: int
    merchant: str
    confirmed_category: str
    predicted_category: Optional[str] = None

@app.post("/classify/feedback")
def save_category_feedback(request: CategoryFeedbackRequest):
    try:
        result = record_user_feedback(
            user_id=request.user_id,
            merchant=request.merchant,
            category=request.confirmed_category,
            predicted_category=request.predicted_category
        )
        return {"status": "success", **result}
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except Exception:
        raise HTTPException(status_code=500, detail="Could not save category feedback.")

# 5) PDF endpoint: keep your existing endpoint and this call:
# pdf_buffer = generate_statement_pdf(transactions, branding="Paisora")
# Return it using your existing StreamingResponse.
