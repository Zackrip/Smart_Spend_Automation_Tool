from fastapi import FastAPI, HTTPException,UploadFile, File
from src.merchant_learning import record_user_feedback
from fastapi.responses import StreamingResponse
from src.statement_pdf_report import generate_statement_pdf
from src.statement_processor import process_phonepe_statement, process_phonepe_transactions
from src.phonepe_csv_parser import extract_phonepe_csv_transactions
from src.statement_api import build_statement_overview
from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import List, Optional
import pandas as pd
import json
from sqlalchemy import text
from db_connection import engine
from main import get_engine_status
from src.anomaly_detection import detect_expense_anomalies
from src.expense_forecasting import forecast_monthly_expenses
from src.budget_analysis import analyze_budgets
from src.savings_recommendations import analyze_savings_goals
from src.notification_parser import extract_transaction
from src.transaction_classifier import classify_transaction
from src.transaction_type_detector import detect_transaction_type
from src.personal_transfer_classifier import classify_personal_transfer, save_personal_contact
from src.ride_payment_reconciliation import detect_ride_event, confirm_ride_payment
# ==========================================
# 1. FASTAPI INITIALIZATION
# ==========================================
app = FastAPI(
    title="Paisora",
    description="Python Data Science Engine",
    version="1.0.0"
)
# ==========================================
# 2. INPUT SCHEMAS
# ==========================================
class Transaction(BaseModel):
    id: int
    user_id: int
    category_id: int
    amount: float
class AnomalyRequest(BaseModel):
    transactions: List[Transaction]
    min_transactions: int = Field(default=4, ge=1)
class MonthlyExpense(BaseModel):
    user_id: int
    month: date
    monthly_expense: float
class ForecastRequest(BaseModel):
    monthly_data: List[MonthlyExpense]
    window: int = Field(default=3, ge=1)
class Budget(BaseModel):
    user_id: int
    category_id: int
    amount_limit: float
    start_date: date
    end_date: date
class BudgetTransaction(BaseModel):
    user_id: int
    category_id: int
    amount: float
    transaction_type: str
    transaction_date: datetime
class Category(BaseModel):
    id: int
    name: str
class BudgetRequest(BaseModel):
    budgets: List[Budget]
    transactions: List[BudgetTransaction]
    categories: List[Category]
    near_limit_pct: float = Field(default=80.0, gt=0, le=100)
class SavingsGoal(BaseModel):
    user_id: int
    name: str
    target_amount: float
    current_amount: float
    target_date: Optional[date] = None
    status: str
class SavingsRequest(BaseModel):
    savings_goals: List[SavingsGoal]
class NotificationRequest(BaseModel):
    notification_text: str
    source: Optional[str] = None
    user_category: Optional[str] = None
    user_id: Optional[int] = None
    notification_title: Optional[str] = None
    package_name: Optional[str] = None
    email_sender: Optional[str] = None


class RidePaymentConfirmationRequest(BaseModel):
    ride_event: dict
    payment_method: str
    payment_status: str = "paid"


class PersonalContactRequest(BaseModel):
    user_id: int
    contact_name: str
    relationship: str
    aliases: List[str] = []


class TransactionIntelligenceRequest(BaseModel):
    transactions: List[dict]
    user_id: Optional[int] = None
    confidence_threshold: float = Field(default=0.70, ge=0.0, le=1.0)

class CategoryFeedbackRequest(BaseModel):
    user_id: int
    merchant: str
    confirmed_category: str
    confirmed_subcategory: str = "Unspecified"
    predicted_category: Optional[str] = None
# ==========================================
# 3. HELPER FUNCTION
# ==========================================
def dataframe_to_records(dataframe):
    return json.loads(
        dataframe.to_json(
            orient="records",
            date_format="iso"
        )
    )
# ==========================================
# 4. HOME ENDPOINT
# ==========================================

@app.get("/")
def home():
    return {
        "message": "Paisora Python Engine",
        "status": "running"
    }
# ==========================================
# 5. HEALTH CHECK ENDPOINT
# ==========================================
@app.get("/health")
def health_check():
    return get_engine_status()
# ==========================================
# 6. ANOMALY DETECTION API
# ==========================================
@app.post("/analyze/anomalies")
def analyze_anomalies(request: AnomalyRequest):
    try:
        data = [
            transaction.model_dump()
            for transaction in request.transactions
        ]
        df = pd.DataFrame(data)
        results = detect_expense_anomalies(
            df,
            min_transactions=request.min_transactions
        )
        anomalies = results[results["anomaly"] == True]
        return {
            "status": "success",
            "total_transactions": len(df),
            "anomalies_detected": len(anomalies),
            "anomalies": dataframe_to_records(anomalies)
        }
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Anomaly detection failed."
        )
# ==========================================
# 7. EXPENSE FORECASTING API
# ==========================================
@app.post("/analyze/forecast")
def analyze_forecast(request: ForecastRequest):
    try:
        data = [
            expense.model_dump()
            for expense in request.monthly_data
        ]
        df = pd.DataFrame(data)
        results = forecast_monthly_expenses(
            df,
            window=request.window
        )
        return {
            "status": "success",
            "users_processed": len(results),
            "forecasts": dataframe_to_records(results)
        }
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Expense forecasting failed."
        )
# ==========================================
# 8. BUDGET ANALYSIS API
# ==========================================
@app.post("/analyze/budgets")
def analyze_budget(request: BudgetRequest):
    try:
        budgets_data = [
            budget.model_dump()
            for budget in request.budgets
        ]
        transactions_data = [
            transaction.model_dump()
            for transaction in request.transactions
        ]
        categories_data = [
            category.model_dump()
            for category in request.categories
        ]
        budgets_df = pd.DataFrame(budgets_data)
        transactions_df = pd.DataFrame(transactions_data)
        categories_df = pd.DataFrame(categories_data)
        results = analyze_budgets(
            budgets=budgets_df,
            transactions=transactions_df,
            categories=categories_df,
            near_limit_pct=request.near_limit_pct)
        return {
            "status": "success",
            "total_budgets": len(results),
            "budgets": dataframe_to_records(results)
        }
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Budget analysis failed.")
# ==========================================
# 9. SAVINGS RECOMMENDATIONS API
# ==========================================
@app.post("/analyze/savings")
def analyze_savings(request: SavingsRequest):
    try:
        data = [
            goal.model_dump()
            for goal in request.savings_goals
        ]
        df = pd.DataFrame(data)
        results = analyze_savings_goals(df)
        return {
            "status": "success",
            "total_goals": len(results),
            "recommendations": dataframe_to_records(results)
        }
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Savings recommendations failed.")

@app.post("/parse/notification")
def parse_notification(request: NotificationRequest):
    try:
        # Preserve sender/title as extraction context where available.
        result = extract_transaction(
            request.notification_text,
            sender=request.notification_title or request.source
        )

        # Service/ride detection has priority over personal-transfer detection.
        ride = detect_ride_event(
            notification_title=request.notification_title,
            notification_text=request.notification_text,
            package_name=request.package_name,
            email_sender=request.email_sender,
            amount=result.get("amount"),
            event_time=result.get("transaction_date")
        )

        detected_type = detect_transaction_type(
            description=request.notification_text,
            direction=result.get("transaction_type")
        )

        if ride is not None:
            classification = {
                "category": ride["category"],
                "main_category": ride["main_category"],
                "subcategory": ride["subcategory"],
                "classification_method": ride["classification_method"],
                "confidence": 0.95,
                "needs_review": ride["ride_status"] != "completed"
            }
            result["ride_event"] = ride
            # Ride completion is not payment confirmation.
            result["needs_user_confirmation"] = ride["needs_user_confirmation"]

        else:
            personal = classify_personal_transfer(
                counterparty=result.get("counterparty"),
                description=request.notification_text,
                direction=result.get("transaction_type"),
                user_id=request.user_id
            )

            if personal is not None:
                classification = personal
            else:
                classification = classify_transaction(
                    counterparty=result.get("counterparty"),
                    notification_text=request.notification_text,
                    transaction_description=request.notification_text,
                    user_category=request.user_category,
                    user_id=request.user_id
                )

        result["category"] = classification["category"]
        result["main_category"] = classification["main_category"]
        result["subcategory"] = classification["subcategory"]
        result["classification_method"] = classification["classification_method"]
        result["confidence"] = classification.get("confidence", 0.0)
        result["transaction_type"] = detected_type["transaction_type"]
        result["transaction_subtype"] = (
            ride.get("transaction_subtype", "ride_payment_pending")
            if ride is not None
            else classification.get("transaction_subtype", detected_type["transaction_subtype"])
        )
        result["needs_review"] = (
            result.get("needs_review", False)
            or classification["needs_review"]
            or detected_type["transaction_type"] == "unknown"
        )
        result["source"] = request.source

        return {"status": "success", "transaction": result}

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except Exception as error:
        print("Notification parsing error:", error)
        raise HTTPException(status_code=500, detail="Notification parsing failed.")


@app.post("/rides/confirm-payment")
def confirm_ride_payment_api(request: RidePaymentConfirmationRequest):
    try:
        return {
            "status": "success",
            "ride": confirm_ride_payment(
                request.ride_event,
                request.payment_method,
                request.payment_status
            )
        }
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@app.post("/contacts")
def create_personal_contact(request: PersonalContactRequest):
    try:
        saved = save_personal_contact(
            user_id=request.user_id,
            contact_name=request.contact_name,
            relationship=request.relationship,
            aliases=request.aliases
        )
        return {"status": "success", "contact": saved}
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


# ==========================================
# DATABASE-BASED ANALYSIS ENDPOINTS
# ==========================================


# ==========================================
# 1. ANOMALY DETECTION FROM POSTGRESQL
# ==========================================

@app.get("/analyze/anomalies/database")
def analyze_database_anomalies(
    user_id: int,
    min_transactions: int = 4
):

    try:
        query = text("""
            SELECT
                id,
                user_id,
                category_id,
                amount
            FROM transactions
            WHERE user_id = :user_id
              AND transaction_type = 'expense'
              AND amount > 0
            ORDER BY transaction_date
        """)

        df = pd.read_sql_query(
            query,
            engine,
            params={"user_id": user_id}
        )

        if df.empty:
            return {
                "status": "success",
                "data_source": "PostgreSQL",
                "user_id": user_id,
                "total_transactions": 0,
                "anomalies_detected": 0,
                "anomalies": []
            }

        results = detect_expense_anomalies(
            df,
            min_transactions=min_transactions
        )

        anomalies = results[
            results["anomaly"] == True
        ]

        return {
            "status": "success",
            "data_source": "PostgreSQL",
            "user_id": user_id,
            "total_transactions": len(df),
            "anomalies_detected": len(anomalies),
            "anomalies": dataframe_to_records(anomalies)
        }

    except Exception as error:
        print("Anomaly database error:", error)

        raise HTTPException(
            status_code=500,
            detail="Database anomaly analysis failed."
        )


# ==========================================
# 2. EXPENSE FORECASTING FROM POSTGRESQL
# ==========================================

@app.get("/analyze/forecast/database")
def analyze_database_forecast(
    user_id: int,
    window: int = 3
):

    try:
        query = text("""
            SELECT
                user_id,
                DATE_TRUNC('month', transaction_date) AS month,
                SUM(amount) AS monthly_expense
            FROM transactions
            WHERE user_id = :user_id
              AND transaction_type = 'expense'
              AND amount > 0
            GROUP BY
                user_id,
                DATE_TRUNC('month', transaction_date)
            ORDER BY month
        """)

        df = pd.read_sql_query(
            query,
            engine,
            params={"user_id": user_id}
        )

        if df.empty:
            return {
                "status": "success",
                "data_source": "PostgreSQL",
                "user_id": user_id,
                "message": "No expense history found.",
                "forecasts": []
            }

        results = forecast_monthly_expenses(
            df,
            window=window
        )

        return {
            "status": "success",
            "data_source": "PostgreSQL",
            "user_id": user_id,
            "months_available": len(df),
            "forecasts": dataframe_to_records(results)
        }

    except Exception as error:
        print("Forecast database error:", error)

        raise HTTPException(
            status_code=500,
            detail="Database expense forecasting failed."
        )


# ==========================================
# 3. BUDGET ANALYSIS FROM POSTGRESQL
# ==========================================

@app.get("/analyze/budgets/database")
def analyze_database_budgets(
    user_id: int,
    near_limit_pct: float = 80.0
):

    try:
        # Fetch user's budgets
        budget_query = text("""
            SELECT
                user_id,
                category_id,
                amount_limit,
                start_date,
                end_date
            FROM budgets
            WHERE user_id = :user_id
        """)

        budgets_df = pd.read_sql_query(
            budget_query,
            engine,
            params={"user_id": user_id}
        )

        if budgets_df.empty:
            return {
                "status": "success",
                "data_source": "PostgreSQL",
                "user_id": user_id,
                "total_budgets": 0,
                "budgets": []
            }

        # Fetch user's transactions
        transaction_query = text("""
            SELECT
                user_id,
                category_id,
                amount,
                transaction_type,
                transaction_date
            FROM transactions
            WHERE user_id = :user_id
              AND transaction_type = 'expense'
              AND amount > 0
        """)

        transactions_df = pd.read_sql_query(
            transaction_query,
            engine,
            params={"user_id": user_id}
        )

        # Fetch category names
        category_query = text("""
            SELECT
                id,
                name
            FROM categories
            WHERE user_id = :user_id
               OR user_id IS NULL
        """)

        categories_df = pd.read_sql_query(
            category_query,
            engine,
            params={"user_id": user_id}
        )

        results = analyze_budgets(
            budgets=budgets_df,
            transactions=transactions_df,
            categories=categories_df,
            near_limit_pct=near_limit_pct
        )

        return {
            "status": "success",
            "data_source": "PostgreSQL",
            "user_id": user_id,
            "total_budgets": len(results),
            "budgets": dataframe_to_records(results)
        }

    except Exception as error:
        print("Budget database error:", error)

        raise HTTPException(
            status_code=500,
            detail="Database budget analysis failed."
        )


# ==========================================
# 4. SAVINGS RECOMMENDATIONS FROM POSTGRESQL
# ==========================================

@app.get("/analyze/savings/database")
def analyze_database_savings(user_id: int):

    try:
        query = text("""
            SELECT
                user_id,
                name,
                target_amount,
                current_amount,
                target_date,
                status
            FROM savings_goals
            WHERE user_id = :user_id
        """)

        df = pd.read_sql_query(
            query,
            engine,
            params={"user_id": user_id}
        )

        if df.empty:
            return {
                "status": "success",
                "data_source": "PostgreSQL",
                "user_id": user_id,
                "total_goals": 0,
                "recommendations": []
            }

        results = analyze_savings_goals(df)

        return {
            "status": "success",
            "data_source": "PostgreSQL",
            "user_id": user_id,
            "total_goals": len(results),
            "recommendations": dataframe_to_records(results)
        }

    except Exception as error:
        print("Savings database error:", error)

        raise HTTPException(
            status_code=500,
            detail="Database savings analysis failed."
        )




@app.post("/import/phonepe-statement")
async def import_phonepe_statement(
    file: UploadFile = File(...),
    user_id: Optional[int] = None
):
    """
    Upload a PhonePe PDF or CSV statement.
    Returns a JSON financial overview and the classified transactions.
    """
    filename = (file.filename or "").lower()
    if not (filename.endswith(".pdf") or filename.endswith(".csv")):
        raise HTTPException(
            status_code=400,
            detail="Please upload a PhonePe PDF or CSV statement."
        )

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")

    try:
        if filename.endswith(".pdf"):
            if not file_bytes.startswith(b"%PDF-"):
                raise HTTPException(status_code=400, detail="Invalid PDF file.")
            result = process_phonepe_statement(file_bytes, user_id=user_id)
            source_format = "pdf"
        else:
            # The CSV parser detects PhonePe's metadata preamble and header.
            parsed_transactions = extract_phonepe_csv_transactions(file_bytes)
            result = process_phonepe_transactions(
                parsed_transactions,
                user_id=user_id
            )
            source_format = "csv"

        if not result.get("transactions"):
            raise HTTPException(status_code=400, detail="No transactions extracted.")

        return {
            "status": "success",
            "source_format": source_format,
            **build_statement_overview(result)
        }

    except HTTPException:
        raise
    except (ValueError, UnicodeDecodeError) as error:
        raise HTTPException(status_code=400, detail=str(error))
    except Exception:
        # Keep internal exception details out of the public API response.
        raise HTTPException(
            status_code=500,
            detail="Statement processing failed. Please check the file and try again."
        )


@app.post("/import/phonepe-statement/report")
async def download_phonepe_statement_report(
    file: UploadFile = File(...),
    user_id: Optional[int] = None
):
    """Generate a PDF report from the uploaded PhonePe PDF or CSV statement."""
    filename = (file.filename or "").lower()
    if not (filename.endswith(".pdf") or filename.endswith(".csv")):
        raise HTTPException(
            status_code=400,
            detail="Please upload a PhonePe PDF or CSV statement."
        )

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")

    try:
        if filename.endswith(".pdf"):
            if not file_bytes.startswith(b"%PDF-"):
                raise HTTPException(status_code=400, detail="Invalid PDF file.")
            result = process_phonepe_statement(file_bytes, user_id=user_id)
        else:
            parsed_transactions = extract_phonepe_csv_transactions(file_bytes)
            result = process_phonepe_transactions(
                parsed_transactions,
                user_id=user_id
            )

        if not result.get("transactions"):
            raise HTTPException(status_code=400, detail="No transactions extracted.")

        pdf_buffer = generate_statement_pdf(
            result["transactions"],
            branding="Paisora"
        )
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition":
                    'attachment; filename="Paisora_Transaction_Report.pdf"'
            }
        )
    except HTTPException:
        raise
    except (ValueError, UnicodeDecodeError) as error:
        raise HTTPException(status_code=400, detail=str(error))
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Statement report generation failed. Please try again."
        )

@app.post("/classify/feedback")
def save_category_feedback(request: CategoryFeedbackRequest):

    try:
        result = record_user_feedback(
            user_id=request.user_id,
            merchant=request.merchant,
            category=request.confirmed_category,
            subcategory=request.confirmed_subcategory
        )

        return {
            "status": "success",
            **result
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Could not save category feedback."
        )

@app.post("/analyze/transaction-intelligence")
def analyze_transaction_intelligence(request: TransactionIntelligenceRequest):
    """Classify and enrich a supplied transaction history with Phase 4 insights."""
    try:
        result = process_phonepe_transactions(
            request.transactions, user_id=request.user_id
        )
        return {
            "status": "success",
            "summary": {
                "total_transactions": result.get("total_transactions", 0),
                "total_expenses": result.get("total_expenses", 0),
                "transactions_needing_review": result.get("transactions_needing_review", 0),
            },
            "intelligence": result.get("intelligence_summary", {}),
            "recurring_payments": result.get("recurring_payments", []),
            "duplicate_candidates": result.get("duplicate_candidates", []),
            "review_queue": result.get("review_queue", []),
            "transactions": result.get("transactions", []),
        }
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Transaction intelligence analysis failed: {str(error)}"
        )
