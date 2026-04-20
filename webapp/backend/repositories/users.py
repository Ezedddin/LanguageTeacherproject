from __future__ import annotations

import sqlite3


def ensure_user(conn: sqlite3.Connection, user_id: str, display_name: str) -> None:
    conn.execute(
        """
        INSERT INTO users (user_id, display_name)
        VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET display_name = excluded.display_name
        """,
        (user_id, display_name),
    )
