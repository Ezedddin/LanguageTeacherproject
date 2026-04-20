from __future__ import annotations

import json
import sqlite3
from typing import Any


def upsert_plan_bundle(
    conn: sqlite3.Connection,
    user_id: str,
    session_id: str,
    assessment: dict[str, Any],
    plan: dict[str, Any],
    tutor_output: dict[str, Any],
    plan_version: int = 1,
) -> None:
    conn.execute(
        """
        INSERT INTO plans (user_id, session_id, plan_version, assessment_json, plan_json, tutor_json)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id, session_id) DO UPDATE SET
            plan_version = excluded.plan_version,
            assessment_json = excluded.assessment_json,
            plan_json = excluded.plan_json,
            tutor_json = excluded.tutor_json,
            created_at = CURRENT_TIMESTAMP
        """,
        (
            user_id,
            session_id,
            plan_version,
            json.dumps(assessment, ensure_ascii=True),
            json.dumps(plan, ensure_ascii=True),
            json.dumps(tutor_output, ensure_ascii=True),
        ),
    )


def get_plan_bundle(
    conn: sqlite3.Connection,
    user_id: str,
    session_id: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]] | None:
    row = conn.execute(
        """
        SELECT assessment_json, plan_json, tutor_json
        FROM plans
        WHERE user_id = ? AND session_id = ?
        """,
        (user_id, session_id),
    ).fetchone()
    if row is None:
        return None
    return (
        json.loads(row["assessment_json"]),
        json.loads(row["plan_json"]),
        json.loads(row["tutor_json"]),
    )
