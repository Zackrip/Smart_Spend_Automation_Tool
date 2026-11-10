from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import List, Optional
import pandas as pd
import json
from main import get_engine_status
from src.anomaly_detection import detect_expense_anomalies
from src.expense_forecasting import forecast_monthly_expenses
from src.budget_analysis import analyze_budgets
from src.savings_recommendations import analyze_savings_goals
# ==========================================
# 1. FASTAPI INITIALIZATION
# ==========================================
app = FastAPI(
    title="SmartSpend AI",
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
        "message": "SmartSpend AI Python Engine",
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