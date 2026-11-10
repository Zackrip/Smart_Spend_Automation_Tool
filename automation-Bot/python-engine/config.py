import os
from pathlib import Path
from dotenv import load_dotenv
# Project root: one level above python-engine
PROJECT_ROOT = Path(__file__).resolve().parent.parent
# Load the existing root .env file
load_dotenv(PROJECT_ROOT / ".env")
# Database configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
# Validate required configuration
if not all([DB_NAME, DB_USER, DB_PASSWORD]):
    raise ValueError(
        "Database configuration is incomplete. Check your root .env file.")
