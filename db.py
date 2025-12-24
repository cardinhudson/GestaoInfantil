"""SQLite database helpers used across the application.

This module intentionally relies on the standard ``sqlite3`` module so that the
same codepath is executed locally and on Streamlit Cloud, ensuring that the
database file is created, reused, and committed safely on every operation.
"""
import logging
import os
import sqlite3
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def _get_db_target_from_env() -> Optional[str]:
    target = os.environ.get("GESTAO_DB")
    if target:
        return target
    try:
        import streamlit as _st  # type: ignore

        secrets = getattr(_st, "secrets", None)
        if isinstance(secrets, dict):
            if secrets.get("GESTAO_DB"):
                return secrets["GESTAO_DB"]
            if secrets.get("DATABASE_URL"):
                return secrets["DATABASE_URL"]
    except Exception:
        return None
    return None


def _resolve_sqlite_path() -> Path:
    target = _get_db_target_from_env() or "gestaoinfantil.db"
    if target.startswith("sqlite://"):
        target = target.replace("sqlite://", "", 1).lstrip("/")
    path = Path(target)
    if not path.is_absolute():
        path = Path(os.getcwd()).joinpath(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path.resolve()


DB_PATH = _resolve_sqlite_path()
logger.info(f"Using SQLite database at {DB_PATH}")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn


def init_db():
    conn = get_connection()
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT,
                roles TEXT NOT NULL DEFAULT 'child',
                password_hash TEXT,
                photo TEXT
            );

            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                points REAL NOT NULL,
                conversion_type TEXT NOT NULL,
                child_id INTEGER NOT NULL,
                submitted_by_id INTEGER,
                validator_id INTEGER,
                validated INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                validated_at TEXT,
                FOREIGN KEY(child_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(submitted_by_id) REFERENCES users(id),
                FOREIGN KEY(validator_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS conversions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                money_per_point REAL NOT NULL DEFAULT 0.5,
                hours_per_point REAL NOT NULL DEFAULT 0.1
            );

            CREATE TABLE IF NOT EXISTS debits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                points_deducted INTEGER NOT NULL DEFAULT 0,
                money_amount REAL,
                hours_amount REAL,
                reason TEXT,
                performed_by_id INTEGER,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(performed_by_id) REFERENCES users(id)
            );
            """
        )
        conn.commit()
    finally:
        conn.close()
