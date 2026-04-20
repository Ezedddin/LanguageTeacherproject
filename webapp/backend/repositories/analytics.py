from __future__ import annotations

import json
import sqlite3
from typing import Any


def log_event(
    conn: sqlite3.Connection,
    user_id: str,
    session_id: str,
    event_name: str,
    event_data: dict[str, Any] | None = None,
) -> None:
    conn.execute(
        """
        INSERT INTO analytics_events (user_id, session_id, event_name, event_data_json)
        VALUES (?, ?, ?, ?)
        """,
        (user_id, session_id, event_name, json.dumps(event_data or {}, ensure_ascii=True)),
    )


def summarize_metrics(
    conn: sqlite3.Connection,
    user_id: str,
    session_id: str,
) -> dict[str, Any]:
    instance_count = conn.execute(
        """
        SELECT COUNT(*) AS n
        FROM lesson_instances
        WHERE user_id = ? AND session_id = ?
        """,
        (user_id, session_id),
    ).fetchone()
    if int(instance_count["n"] or 0) > 0:
        row = conn.execute(
            """
            SELECT
                COUNT(*) AS total_lessons,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS completed_lessons,
                COALESCE(AVG(accuracy), 0) AS avg_accuracy,
                COALESCE(SUM(xp_earned), 0) AS total_xp
            FROM lesson_instances
            WHERE user_id = ? AND session_id = ?
            """,
            (user_id, session_id),
        ).fetchone()
    else:
        row = conn.execute(
            """
            SELECT
                COUNT(*) AS total_lessons,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS completed_lessons,
                COALESCE(AVG(accuracy), 0) AS avg_accuracy,
                COALESCE(SUM(xp_earned), 0) AS total_xp
            FROM lesson_progress
            WHERE user_id = ? AND session_id = ?
            """,
            (user_id, session_id),
        ).fetchone()
    total = int(row["total_lessons"] or 0)
    completed = int(row["completed_lessons"] or 0)
    completion_rate = round((completed / total) * 100, 1) if total else 0.0
    return {
        "total_lessons": total,
        "completed_lessons": completed,
        "completion_rate": completion_rate,
        "avg_accuracy": round(float(row["avg_accuracy"] or 0), 1),
        "total_xp": int(row["total_xp"] or 0),
    }
