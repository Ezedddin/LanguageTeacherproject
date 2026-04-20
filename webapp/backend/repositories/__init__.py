from .analytics import log_event, summarize_metrics
from .lessons import (
    complete_lesson,
    create_review_items,
    get_lesson_design,
    get_lessons_with_status,
    get_review_due_today,
    initialize_lesson_progress,
    is_lesson_locked,
    record_phase_attempt,
    start_lesson,
    upsert_lesson_instances,
)
from .plans import get_plan_bundle, upsert_plan_bundle
from .users import ensure_user

__all__ = [
    "complete_lesson",
    "create_review_items",
    "ensure_user",
    "get_lesson_design",
    "get_lessons_with_status",
    "get_plan_bundle",
    "get_review_due_today",
    "initialize_lesson_progress",
    "is_lesson_locked",
    "log_event",
    "record_phase_attempt",
    "start_lesson",
    "summarize_metrics",
    "upsert_lesson_instances",
    "upsert_plan_bundle",
]
