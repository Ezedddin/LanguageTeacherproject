from __future__ import annotations

import sqlite3
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parent
DB_PATH = BACKEND_DIR / "app.db"


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 30000;")
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db() -> None:
    schema = """
    CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        display_name TEXT NOT NULL DEFAULT 'Guest Learner',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        session_id TEXT NOT NULL,
        plan_version INTEGER NOT NULL DEFAULT 1,
        assessment_json TEXT NOT NULL,
        plan_json TEXT NOT NULL,
        tutor_json TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, session_id),
        FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS lesson_progress (
        user_id TEXT NOT NULL,
        session_id TEXT NOT NULL,
        week INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'not_started',
        last_phase INTEGER NOT NULL DEFAULT 0,
        accuracy REAL NOT NULL DEFAULT 0,
        xp_earned INTEGER NOT NULL DEFAULT 0,
        started_at TEXT,
        completed_at TEXT,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY(user_id, session_id, week)
    );

    CREATE TABLE IF NOT EXISTS lesson_attempts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        session_id TEXT NOT NULL,
        week INTEGER NOT NULL,
        phase TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        score REAL NOT NULL DEFAULT 0,
        hints_used INTEGER NOT NULL DEFAULT 0,
        retries INTEGER NOT NULL DEFAULT 0,
        duration_seconds INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS lesson_instances (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        session_id TEXT NOT NULL,
        lesson_id TEXT NOT NULL,
        week INTEGER NOT NULL,
        lesson_number INTEGER NOT NULL,
        sequence_index INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'not_started',
        last_phase INTEGER NOT NULL DEFAULT 0,
        accuracy REAL NOT NULL DEFAULT 0,
        xp_earned INTEGER NOT NULL DEFAULT 0,
        lesson_json TEXT NOT NULL,
        started_at TEXT,
        completed_at TEXT,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, session_id, lesson_id)
    );

    CREATE TABLE IF NOT EXISTS review_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        session_id TEXT NOT NULL,
        topic TEXT NOT NULL,
        source_week INTEGER NOT NULL,
        error_count INTEGER NOT NULL DEFAULT 1,
        status TEXT NOT NULL DEFAULT 'due',
        next_due_at TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS analytics_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        session_id TEXT NOT NULL,
        event_name TEXT NOT NULL,
        event_data_json TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """
    with get_conn() as conn:
        conn.executescript(schema)
