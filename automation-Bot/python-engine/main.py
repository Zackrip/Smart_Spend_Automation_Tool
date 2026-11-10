from db_connection import engine
from src.anomaly_detection import detect_expense_anomalies
from src.expense_forecasting import forecast_monthly_expenses
from src.budget_analysis import analyze_budgets
from src.savings_recommendations import analyze_savings_goals
def check_engine_connection():
    """Check whether the Python engine can access PostgreSQL."""
    from sqlalchemy import text

    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return True
def get_engine_status():
    """Return the status of the Python data science engine."""
    try:
        check_engine_connection()
        return {
            "status": "success",
            "message": "SmartSpend AI Python engine is running",
            "database": "connected",
            "modules": [
                "anomaly_detection",
                "expense_forecasting",
                "budget_analysis",
                "savings_recommendations"]}
    except Exception as error:
        return {
            "status": "error",
            "message": str(error),
            "database": "disconnected"}
if __name__ == "__main__":
    print(get_engine_status())
