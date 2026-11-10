from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from config import (
    DB_HOST,
    DB_PORT,
    DB_NAME,
    DB_USER,
    DB_PASSWORD)
# Safely construct PostgreSQL connection URL
database_url = URL.create(
    drivername="postgresql+psycopg2",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=int(DB_PORT),
    database=DB_NAME)
# Create SQLAlchemy engine
engine = create_engine(
    database_url,
    pool_pre_ping=True)
def test_connection():
    try:
        with engine.connect() as connection:
            result = connection.execute(
                text("SELECT 1")
            ).scalar()
            if result == 1:
                print("PostgreSQL connection successful!")
                return True
    except Exception as error:
        print("Database connection failed:", error)
        return False
    return False