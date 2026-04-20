from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any


def initialize_lesson_progress(
    conn: sqlite3.Connection,
    user_id: str,
    session_id: str,
    duration_weeks: int,
) -> None:
    for week in range(1, duration_weeks + 1):
        conn.execute(
            """
            INSERT OR IGNORE INTO lesson_progress (user_id, session_id, week, status)
            VALUES (?, ?, ?, 'not_started')
            """,
            (user_id, session_id, week),
        )


def get_lessons_with_status(
    conn: sqlite3.Connection,
    user_id: str,
    session_id: str,
) -> list[dict[str, Any]]:
    lesson_rows = conn.execute(
        """
        SELECT lesson_id, week, lesson_number, sequence_index, status, last_phase, accuracy, xp_earned,
               started_at, completed_at, lesson_json
        FROM lesson_instances
        WHERE user_id = ? AND session_id = ?
        ORDER BY sequence_index ASC
        """,
        (user_id, session_id),
    ).fetchall()
    if lesson_rows:
        items: list[dict[str, Any]] = []
        for row in lesson_rows:
            payload = json.loads(row["lesson_json"])
            items.append(
                {
                    "lesson_id": row["lesson_id"],
                    "week": row["week"],
                    "lesson_number": row["lesson_number"],
                    "status": row["status"],
                    "last_phase": row["last_phase"],
                    "accuracy": row["accuracy"],
                    "xp_earned": row["xp_earned"],
                    "started_at": row["started_at"],
                    "completed_at": row["completed_at"],
                    **payload,
                }
            )
        return items

    rows = conn.execute(
        """
        SELECT week, status, last_phase, accuracy, xp_earned, started_at, completed_at
        FROM lesson_progress
        WHERE user_id = ? AND session_id = ?
        ORDER BY week ASC
        """,
        (user_id, session_id),
    ).fetchall()
    return [dict(row) for row in rows]


def is_lesson_locked(
    conn: sqlite3.Connection,
    user_id: str,
    session_id: str,
    week: int | None = None,
    lesson_id: str | None = None,
) -> bool:
    if lesson_id:
        row = conn.execute(
            """
            SELECT sequence_index
            FROM lesson_instances
            WHERE user_id = ? AND session_id = ? AND lesson_id = ?
            """,
            (user_id, session_id, lesson_id),
        ).fetchone()
        if row is None:
            return False
        sequence_index = int(row["sequence_index"])
        if sequence_index <= 1:
            return False
        prev = conn.execute(
            """
            SELECT status
            FROM lesson_instances
            WHERE user_id = ? AND session_id = ? AND sequence_index = ?
            """,
            (user_id, session_id, sequence_index - 1),
        ).fetchone()
        if prev is None:
            return False
        return prev["status"] != "completed"

    if week is None or week <= 1:
        return False
    row = conn.execute(
        """
        SELECT status
        FROM lesson_progress
        WHERE user_id = ? AND session_id = ? AND week = ?
        """,
        (user_id, session_id, week - 1),
    ).fetchone()
    if row is None:
        return False
    return row["status"] != "completed"


def start_lesson(
    conn: sqlite3.Connection,
    user_id: str,
    session_id: str,
    week: int | None = None,
    lesson_id: str | None = None,
) -> tuple[str, int]:
    if lesson_id:
        row = conn.execute(
            """
            SELECT status, last_phase
            FROM lesson_instances
            WHERE user_id = ? AND session_id = ? AND lesson_id = ?
            """,
            (user_id, session_id, lesson_id),
        ).fetchone()
        if row is None:
            return "in_progress", 0
        if row["status"] == "completed":
            return "already_completed", int(row["last_phase"] or 5)
        conn.execute(
            """
            UPDATE lesson_instances
            SET status = 'in_progress',
                started_at = COALESCE(started_at, CURRENT_TIMESTAMP),
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ? AND session_id = ? AND lesson_id = ?
            """,
            (user_id, session_id, lesson_id),
        )
        return "in_progress", int(row["last_phase"] or 0)

    if week is None:
        return "in_progress", 0
    row = conn.execute(
        """
        SELECT status, last_phase
        FROM lesson_progress
        WHERE user_id = ? AND session_id = ? AND week = ?
        """,
        (user_id, session_id, week),
    ).fetchone()
    if row is None:
        conn.execute(
            """
            INSERT INTO lesson_progress (user_id, session_id, week, status, started_at)
            VALUES (?, ?, ?, 'in_progress', CURRENT_TIMESTAMP)
            """,
            (user_id, session_id, week),
        )
        return "in_progress", 0
    if row["status"] == "completed":
        return "already_completed", int(row["last_phase"] or 5)
    conn.execute(
        """
        UPDATE lesson_progress
        SET status = 'in_progress',
            started_at = COALESCE(started_at, CURRENT_TIMESTAMP),
            updated_at = CURRENT_TIMESTAMP
        WHERE user_id = ? AND session_id = ? AND week = ?
        """,
        (user_id, session_id, week),
    )
    return "in_progress", int(row["last_phase"] or 0)


def record_phase_attempt(
    conn: sqlite3.Connection,
    user_id: str,
    session_id: str,
    week: int,
    phase: str,
    payload: dict[str, Any],
    score: float,
    hints_used: int,
    retries: int,
    duration_seconds: int,
    lesson_id: str | None = None,
) -> int:
    if lesson_id:
        phase_map = {
            "warm_up": 1,
            "input": 2,
            "guided_practice": 3,
            "output_speaking": 4,
            "feedback_correction": 5,
        }
        phase_index = phase_map.get(phase, 0)
        conn.execute(
            """
            INSERT INTO lesson_attempts
            (user_id, session_id, week, phase, payload_json, score, hints_used, retries, duration_seconds)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                session_id,
                week,
                phase,
                json.dumps(payload, ensure_ascii=True),
                score,
                hints_used,
                retries,
                duration_seconds,
            ),
        )
        conn.execute(
            """
            UPDATE lesson_instances
            SET status = 'in_progress',
                last_phase = CASE WHEN last_phase < ? THEN ? ELSE last_phase END,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ? AND session_id = ? AND lesson_id = ?
            """,
            (phase_index, phase_index, user_id, session_id, lesson_id),
        )
        row = conn.execute(
            """
            SELECT last_phase
            FROM lesson_instances
            WHERE user_id = ? AND session_id = ? AND lesson_id = ?
            """,
            (user_id, session_id, lesson_id),
        ).fetchone()
        return int(row["last_phase"] or phase_index)

    conn.execute(
        """
        INSERT INTO lesson_attempts
        (user_id, session_id, week, phase, payload_json, score, hints_used, retries, duration_seconds)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            session_id,
            week,
            phase,
            json.dumps(payload, ensure_ascii=True),
            score,
            hints_used,
            retries,
            duration_seconds,
        ),
    )
    phase_map = {
        "warm_up": 1,
        "input": 2,
        "guided_practice": 3,
        "output_speaking": 4,
        "feedback_correction": 5,
    }
    phase_index = phase_map.get(phase, 0)
    conn.execute(
        """
        UPDATE lesson_progress
        SET status = 'in_progress',
            last_phase = CASE WHEN last_phase < ? THEN ? ELSE last_phase END,
            updated_at = CURRENT_TIMESTAMP
        WHERE user_id = ? AND session_id = ? AND week = ?
        """,
        (phase_index, phase_index, user_id, session_id, week),
    )
    row = conn.execute(
        """
        SELECT last_phase
        FROM lesson_progress
        WHERE user_id = ? AND session_id = ? AND week = ?
        """,
        (user_id, session_id, week),
    ).fetchone()
    return int(row["last_phase"] or phase_index)


def create_review_items(
    conn: sqlite3.Connection,
    user_id: str,
    session_id: str,
    week: int,
    weak_topics: list[str],
) -> int:
    count = 0
    now = datetime.now(tz=timezone.utc)
    for index, topic in enumerate(weak_topics):
        due_at = now + timedelta(days=index + 1)
        conn.execute(
            """
            INSERT INTO review_items (user_id, session_id, topic, source_week, error_count, next_due_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                session_id,
                topic,
                week,
                1,
                due_at.isoformat(),
            ),
        )
        count += 1
    return count


def complete_lesson(
    conn: sqlite3.Connection,
    user_id: str,
    session_id: str,
    week: int,
    accuracy: float,
    xp_earned: int,
    lesson_id: str | None = None,
) -> None:
    if lesson_id:
        conn.execute(
            """
            UPDATE lesson_instances
            SET status = 'completed',
                last_phase = 5,
                accuracy = ?,
                xp_earned = ?,
                completed_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ? AND session_id = ? AND lesson_id = ?
            """,
            (accuracy, xp_earned, user_id, session_id, lesson_id),
        )
        return

    conn.execute(
        """
        UPDATE lesson_progress
        SET status = 'completed',
            last_phase = 5,
            accuracy = ?,
            xp_earned = ?,
            completed_at = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP
        WHERE user_id = ? AND session_id = ? AND week = ?
        """,
        (accuracy, xp_earned, user_id, session_id, week),
    )


def get_review_due_today(
    conn: sqlite3.Connection,
    user_id: str,
    session_id: str,
) -> list[dict[str, Any]]:
    now_iso = datetime.now(tz=timezone.utc).isoformat()
    rows = conn.execute(
        """
        SELECT id, topic, source_week, next_due_at, status, error_count
        FROM review_items
        WHERE user_id = ? AND session_id = ? AND status = 'due' AND next_due_at <= ?
        ORDER BY next_due_at ASC
        """,
        (user_id, session_id, now_iso),
    ).fetchall()
    return [dict(row) for row in rows]


def get_lesson_design(
    conn: sqlite3.Connection,
    user_id: str,
    session_id: str,
    lesson_id: str,
) -> dict[str, Any] | None:
    """Return the full designed lesson JSON for a specific lesson_id, or None if not found."""
    row = conn.execute(
        """
        SELECT lesson_json
        FROM lesson_instances
        WHERE user_id = ? AND session_id = ? AND lesson_id = ?
        """,
        (user_id, session_id, lesson_id),
    ).fetchone()
    if row is None:
        return None
    return json.loads(row["lesson_json"])


def upsert_lesson_instances(
    conn: sqlite3.Connection,
    user_id: str,
    session_id: str,
    curriculum_lessons: list[dict[str, Any]],
) -> None:
    for sequence_index, lesson in enumerate(curriculum_lessons, start=1):
        lesson_id = str(lesson.get("lesson_id"))
        week = int(lesson.get("week", 1))
        lesson_number = int(lesson.get("lesson_number", 1))
        conn.execute(
            """
            INSERT INTO lesson_instances
            (user_id, session_id, lesson_id, week, lesson_number, sequence_index, lesson_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, session_id, lesson_id) DO UPDATE SET
                week = excluded.week,
                lesson_number = excluded.lesson_number,
                sequence_index = excluded.sequence_index,
                lesson_json = excluded.lesson_json,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                user_id,
                session_id,
                lesson_id,
                week,
                lesson_number,
                sequence_index,
                json.dumps(lesson, ensure_ascii=True),
            ),
        )
