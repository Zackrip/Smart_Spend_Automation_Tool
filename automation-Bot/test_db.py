import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "python-engine"))

from db_connection import test_connection

test_connection()
