import os
import sqlite3

def get_db_path() -> str:
    return os.getenv("DB_PATH", "draftedi.db")

def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn