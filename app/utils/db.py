"""Database connection utilities"""
import sqlite3
from pathlib import Path

def get_db_connection():
    """Get a connection to the SQLite database"""
    db_path = Path(__file__).parent.parent.parent / 'data' / 'salesforce_data.db'
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn