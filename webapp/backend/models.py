from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class GuestLoginRequest(BaseModel):
    display_name: str = Field(default="Guest Learner", min_length=1, max_length=80)


class GuestLoginResponse(BaseModel):
    user_id: str
    session_id: str
    display_name: str


class LessonStartRequest(BaseModel):
    user_id: str
    session_id: str
    week: int | None = Field(default=None, ge=1, le=52)
    lesson_id: str | None = None


class LessonStartResponse(BaseModel):
    status: Literal["in_progress", "already_completed", "locked"]
    week: int | None
    lesson_id: str | None = None
    last_phase: int


class PhaseSubmitRequest(BaseModel):
    user_id: str
    session_id: str
    week: int | None = Field(default=None, ge=1, le=52)
    lesson_id: str | None = None
    phase: str
    payload: dict[str, Any] = Field(default_factory=dict)
    score: float = Field(default=0.0, ge=0.0, le=100.0)
    hints_used: int = Field(default=0, ge=0)
    retries: int = Field(default=0, ge=0)
    duration_seconds: int = Field(default=0, ge=0)


class PhaseSubmitResponse(BaseModel):
    status: Literal["recorded"]
    week: int | None
    lesson_id: str | None = None
    phase: str
    last_phase: int


class LessonCompleteRequest(BaseModel):
    user_id: str
    session_id: str
    week: int | None = Field(default=None, ge=1, le=52)
    lesson_id: str | None = None
    accuracy: float = Field(default=0.0, ge=0.0, le=100.0)
    xp_earned: int = Field(default=0, ge=0)
    weak_topics: list[str] = Field(default_factory=list)


class LessonCompleteResponse(BaseModel):
    status: Literal["completed"]
    week: int | None
    lesson_id: str | None = None
    review_items_created: int


class DashboardResponse(BaseModel):
    user_id: str
    session_id: str
    assessment: dict[str, Any]
    plan: dict[str, Any]
    tutor_output: dict[str, Any]
    lessons: list[dict[str, Any]]
    curriculum_lessons: list[dict[str, Any]] = Field(default_factory=list)
    review_due_today: list[dict[str, Any]]
    metrics: dict[str, Any]
