import os
import sqlite3

def get_db_path() -> str:
    return os.getenv("DB_PATH", "draftedi.db")

def get_edi_db_path() -> str:
    return os.getenv("EDI_DB_BASE_PATH", "/var/www/draftedi/edi_db/")

def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path(), timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("PRAGMA busy_timeout = 30000;")

    return conn

def connect_edi(version: str) -> sqlite3.Connection:
    conn = sqlite3.connect(os.path.join(get_edi_db_path(),f'x12-{version}.db'), timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("PRAGMA busy_timeout = 30000;")

    return conn