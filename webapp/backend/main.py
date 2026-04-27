from __future__ import annotations
# pyright: reportMissingImports=false

import json
import os
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent.parent
LESSON_DESIGNER_DIR = PROJECT_ROOT / "lesson-designer-agent"
TUTOR_DIR = PROJECT_ROOT / "tutor-agent"

# New src agents (Gemini for assessment, OpenAI for planning + tutor)
SRC_DIR = PROJECT_ROOT / "src"
for candidate in (PROJECT_ROOT, SRC_DIR, LESSON_DESIGNER_DIR, TUTOR_DIR):
    value = str(candidate)
    if candidate.exists() and value not in sys.path:
        sys.path.insert(0, value)

from src.agents.assessment_agent import run_assessment  # noqa: E402
from src.agents.planning_agent import run_planning, LearningPlan  # noqa: E402
from src.agents.tutor_agent import (  # noqa: E402
    run_tutor_turn,
    SessionMemory,
    AssessmentResult,
)
from lesson_designer_agent import LessonDesignerAgent  # noqa: E402
from tts_tool import pyttsx3_tts_tool  # noqa: E402
from db import init_db, get_conn  # noqa: E402
from models import (  # noqa: E402
    DashboardResponse,
    GuestLoginRequest,
    GuestLoginResponse,
    LessonCompleteRequest,
    LessonCompleteResponse,
    LessonStartRequest,
    LessonStartResponse,
    PhaseSubmitRequest,
    PhaseSubmitResponse,
)
from repositories import (  # noqa: E402
    complete_lesson,
    create_review_items,
    ensure_user,
    get_lesson_design,
    get_lessons_with_status,
    get_plan_bundle,
    get_review_due_today,
    initialize_lesson_progress,
    is_lesson_locked,
    log_event,
    record_phase_attempt,
    start_lesson,
    summarize_metrics,
    upsert_lesson_instances,
    upsert_plan_bundle,
)


def load_local_env() -> None:
    env_file = PROJECT_ROOT / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#") or "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


load_local_env()
init_db()

app = FastAPI(title="Language Teacher API", version="0.1.0")

_CORS_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:4173",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:4173",
    "http://localhost:3000",
]
_extra = os.getenv("CORS_ORIGINS", "")
if _extra:
    _CORS_ORIGINS.extend(o.strip() for o in _extra.split(",") if o.strip())

app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)


class PipelineRequest(BaseModel):
    user_id: str = Field(default="demo-user")
    session_id: str = Field(default="session-1")
    answer1: str
    answer2: str
    answer3: str
    answer4: str
    user_input: str = Field(
        default="I am ready to start. Give me my first personalized practice step.",
        description="Optional current learner message for Bot 3.",
    )
    speak_language: str = Field(default="English")
    learn_language: str = Field(default="English")
    lessons_per_week: int = Field(default=2, ge=2, le=3)


class PipelineResponse(BaseModel):
    assessment: dict[str, Any]
    plan: dict[str, Any]
    tutor_output: dict[str, Any]
    curriculum_lessons: list[dict[str, Any]]


class TutorChatRequest(BaseModel):
    user_id: str
    session_id: str
    user_message: str
    lesson_id: str | None = Field(
        default=None,
        description="If set, the tutor loads the Bot-4 lesson design and follows its phases.",
    )
    conversation: list[dict[str, Any]] = Field(default_factory=list)
    memory: dict[str, Any] = Field(default_factory=dict)
    exercise_history: list[dict[str, Any]] = Field(default_factory=list)


class TutorChatResponse(BaseModel):
    message: str
    exercise: dict[str, Any] | None
    feedback: dict[str, Any] | None
    session_complete: bool
    progress_note: str
    conversation: list[dict[str, Any]]
    memory: dict[str, Any]
    exercise_history: list[dict[str, Any]]


class TTSRequest(BaseModel):
    text: str = Field(min_length=1, max_length=4000)
    rate: int = Field(default=180, ge=80, le=260)
    volume: float = Field(default=1.0, ge=0.0, le=1.0)


def _now_session_id() -> str:
    ts = datetime.now(tz=timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"session-{ts}-{uuid4().hex[:8]}"


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/auth/guest-login", response_model=GuestLoginResponse)
def guest_login(payload: GuestLoginRequest) -> GuestLoginResponse:
    user_id = f"guest-{uuid4().hex[:8]}"
    session_id = _now_session_id()
    try:
        with get_conn() as conn:
            ensure_user(conn, user_id=user_id, display_name=payload.display_name)
            log_event(
                conn,
                user_id=user_id,
                session_id=session_id,
                event_name="guest_login",
                event_data={"display_name": payload.display_name},
            )
    except sqlite3.OperationalError as db_exc:
        if "database is locked" in str(db_exc).lower():
            raise HTTPException(
                status_code=503,
                detail="Database is busy: database is locked",
            ) from db_exc
        raise
    return GuestLoginResponse(
        user_id=user_id,
        session_id=session_id,
        display_name=payload.display_name,
    )


@app.post("/api/pipeline", response_model=PipelineResponse)
def run_pipeline(payload: PipelineRequest) -> PipelineResponse:
    try:
        # Bot 1 — Gemini assessment
        assessment = run_assessment(
            [payload.answer1, payload.answer2, payload.answer3, payload.answer4],
            target_language=payload.learn_language,
        )

        # Bot 2 — OpenAI planning (LangGraph conditional routing)
        plan = run_planning(assessment, target_language=payload.learn_language)

        # Bot 3 — OpenAI tutor initial greeting
        init_resp, init_memory, init_conv, init_hist = run_tutor_turn(
            user_message=payload.user_input,
            assessment=assessment,
            plan=plan,
            memory=SessionMemory(),
            conversation=[],
            exercise_history=[],
        )

        # Bot 4 — Lesson designer (unchanged, keeps existing provider)
        bot4 = LessonDesignerAgent()
        curriculum = bot4.design_curriculum(
            assessment=assessment,
            plan=plan,
            lessons_per_week=payload.lessons_per_week,
            target_language=payload.learn_language,
        )
    except Exception as exc:
        message = str(exc)
        if "database is locked" in message.lower():
            raise HTTPException(
                status_code=503,
                detail=(
                    "Database is temporarily busy. Please retry in a few seconds."
                ),
            ) from exc
        if "RESOURCE_EXHAUSTED" in message or "quota" in message.lower():
            raise HTTPException(
                status_code=503,
                detail=(
                    "AI quota reached for one of the model providers. "
                    "Please retry later or switch provider/key."
                ),
            ) from exc
        raise HTTPException(
            status_code=500,
            detail=f"Pipeline failed: {message}",
        ) from exc

    assessment_dump = assessment.model_dump()
    plan_dump = plan.model_dump()
    tutor_dump = {
        "message": init_resp.message,
        "tutor_message": init_resp.message,           # backward-compat
        "suggested_exercise": (
            init_resp.exercise.prompt if init_resp.exercise else ""
        ),
        "focus_topic": (
            init_resp.exercise.topic if init_resp.exercise else ""
        ),
        "difficulty_adjustment": (
            init_resp.exercise.difficulty if init_resp.exercise else "same"
        ),
        "progress_note": init_resp.progress_note,
        "session_complete": init_resp.session_complete,
        "initial_memory": init_memory.model_dump(),
        "initial_conversation": init_conv,
        "initial_exercise_history": init_hist,
    }
    curriculum_dump = [lesson.model_dump() for lesson in curriculum.lessons]

    try:
        for attempt in range(3):
            try:
                with get_conn() as conn:
                    ensure_user(conn, user_id=payload.user_id, display_name=payload.user_id)
                    upsert_plan_bundle(
                        conn,
                        user_id=payload.user_id,
                        session_id=payload.session_id,
                        assessment=assessment_dump,
                        plan=plan_dump,
                        tutor_output=tutor_dump,
                        plan_version=1,
                    )
                    initialize_lesson_progress(
                        conn,
                        user_id=payload.user_id,
                        session_id=payload.session_id,
                        duration_weeks=int(plan.duration_weeks),
                    )
                    upsert_lesson_instances(
                        conn,
                        user_id=payload.user_id,
                        session_id=payload.session_id,
                        curriculum_lessons=curriculum_dump,
                    )
                    log_event(
                        conn,
                        user_id=payload.user_id,
                        session_id=payload.session_id,
                        event_name="pipeline_generated",
                        event_data={
                            "level": assessment.level,
                            "duration_weeks": plan.duration_weeks,
                            "lessons_per_week": payload.lessons_per_week,
                            "curriculum_lessons": len(curriculum_dump),
                        },
                    )
                break
            except sqlite3.OperationalError as db_exc:
                if "database is locked" not in str(db_exc).lower() or attempt == 2:
                    raise
                time.sleep(0.2 * (attempt + 1))
    except sqlite3.OperationalError as db_exc:
        raise HTTPException(
            status_code=503,
            detail=f"Database is busy: {db_exc}",
        ) from db_exc

    return PipelineResponse(
        assessment=assessment_dump,
        plan=plan_dump,
        tutor_output=tutor_dump,
        curriculum_lessons=curriculum_dump,
    )


@app.post("/api/tutor/chat", response_model=TutorChatResponse)
def tutor_chat(payload: TutorChatRequest) -> TutorChatResponse:
    """Interactive tutor chat endpoint. Frontend passes conversation + memory each turn."""
    with get_conn() as conn:
        bundle = get_plan_bundle(conn, user_id=payload.user_id, session_id=payload.session_id)
        if bundle is None:
            raise HTTPException(
                status_code=404,
                detail="No learning plan found. Run /api/pipeline first.",
            )
        assessment_dict, plan_dict, _ = bundle

    assessment = AssessmentResult(**assessment_dict)
    plan = LearningPlan(**plan_dict)
    memory = SessionMemory(**(payload.memory or {}))

    # Load the Bot-4 lesson design if a lesson_id was provided
    lesson_context: dict | None = None
    if payload.lesson_id:
        with get_conn() as conn:
            lesson_context = get_lesson_design(
                conn,
                user_id=payload.user_id,
                session_id=payload.session_id,
                lesson_id=payload.lesson_id,
            )

    resp, new_memory, new_conv, new_hist = run_tutor_turn(
        user_message=payload.user_message,
        assessment=assessment,
        plan=plan,
        memory=memory,
        conversation=payload.conversation,
        exercise_history=payload.exercise_history,
        lesson_context=lesson_context,
    )

    return TutorChatResponse(
        message=resp.message,
        exercise=resp.exercise.model_dump() if resp.exercise else None,
        feedback=resp.feedback.model_dump() if resp.feedback else None,
        session_complete=resp.session_complete,
        progress_note=resp.progress_note,
        conversation=new_conv,
        memory=new_memory.model_dump(),
        exercise_history=new_hist,
    )


@app.get("/api/dashboard", response_model=DashboardResponse)
def get_dashboard(
    user_id: str = Query(...),
    session_id: str = Query(...),
) -> DashboardResponse:
    with get_conn() as conn:
        bundle = get_plan_bundle(conn, user_id=user_id, session_id=session_id)
        if bundle is None:
            raise HTTPException(
                status_code=404,
                detail="No learning plan found for this user/session.",
            )
        assessment, plan, tutor_output = bundle
        lessons = get_lessons_with_status(conn, user_id=user_id, session_id=session_id)
        review_due_today = get_review_due_today(conn, user_id=user_id, session_id=session_id)
        metrics = summarize_metrics(conn, user_id=user_id, session_id=session_id)
    return DashboardResponse(
        user_id=user_id,
        session_id=session_id,
        assessment=assessment,
        plan=plan,
        tutor_output=tutor_output,
        lessons=lessons,
        curriculum_lessons=lessons,
        review_due_today=review_due_today,
        metrics=metrics,
    )


@app.post("/api/lesson/start", response_model=LessonStartResponse)
def lesson_start(payload: LessonStartRequest) -> LessonStartResponse:
    with get_conn() as conn:
        if payload.lesson_id is None and payload.week is None:
            raise HTTPException(status_code=400, detail="Provide lesson_id or week.")
        if is_lesson_locked(
            conn,
            user_id=payload.user_id,
            session_id=payload.session_id,
            week=payload.week,
            lesson_id=payload.lesson_id,
        ):
            return LessonStartResponse(
                status="locked",
                week=payload.week,
                lesson_id=payload.lesson_id,
                last_phase=0,
            )
        status, last_phase = start_lesson(
            conn,
            user_id=payload.user_id,
            session_id=payload.session_id,
            week=payload.week,
            lesson_id=payload.lesson_id,
        )
        log_event(
            conn,
            user_id=payload.user_id,
            session_id=payload.session_id,
            event_name="lesson_started",
            event_data={
                "week": payload.week,
                "lesson_id": payload.lesson_id,
                "status": status,
            },
        )
    return LessonStartResponse(
        status=status,
        week=payload.week,
        lesson_id=payload.lesson_id,
        last_phase=last_phase,
    )


@app.post("/api/lesson/phase-submit", response_model=PhaseSubmitResponse)
def lesson_phase_submit(payload: PhaseSubmitRequest) -> PhaseSubmitResponse:
    with get_conn() as conn:
        if payload.lesson_id is None and payload.week is None:
            raise HTTPException(status_code=400, detail="Provide lesson_id or week.")
        resolved_week = payload.week or 1
        last_phase = record_phase_attempt(
            conn,
            user_id=payload.user_id,
            session_id=payload.session_id,
            week=resolved_week,
            phase=payload.phase,
            payload=payload.payload,
            score=payload.score,
            hints_used=payload.hints_used,
            retries=payload.retries,
            duration_seconds=payload.duration_seconds,
            lesson_id=payload.lesson_id,
        )
        log_event(
            conn,
            user_id=payload.user_id,
            session_id=payload.session_id,
            event_name="phase_completed",
            event_data={
                "week": payload.week,
                "lesson_id": payload.lesson_id,
                "phase": payload.phase,
                "score": payload.score,
            },
        )
    return PhaseSubmitResponse(
        status="recorded",
        week=payload.week,
        lesson_id=payload.lesson_id,
        phase=payload.phase,
        last_phase=last_phase,
    )


@app.post("/api/lesson/complete", response_model=LessonCompleteResponse)
def lesson_complete(payload: LessonCompleteRequest) -> LessonCompleteResponse:
    with get_conn() as conn:
        if payload.lesson_id is None and payload.week is None:
            raise HTTPException(status_code=400, detail="Provide lesson_id or week.")
        resolved_week = payload.week or 1
        complete_lesson(
            conn,
            user_id=payload.user_id,
            session_id=payload.session_id,
            week=resolved_week,
            accuracy=payload.accuracy,
            xp_earned=payload.xp_earned,
            lesson_id=payload.lesson_id,
        )
        review_count = create_review_items(
            conn,
            user_id=payload.user_id,
            session_id=payload.session_id,
            week=resolved_week,
            weak_topics=payload.weak_topics,
        )
        log_event(
            conn,
            user_id=payload.user_id,
            session_id=payload.session_id,
            event_name="lesson_completed",
            event_data={
                "week": payload.week,
                "lesson_id": payload.lesson_id,
                "accuracy": payload.accuracy,
                "xp_earned": payload.xp_earned,
                "review_items_created": review_count,
            },
        )
    return LessonCompleteResponse(
        status="completed",
        week=payload.week,
        lesson_id=payload.lesson_id,
        review_items_created=review_count,
    )


@app.post("/api/tools/tts")
def run_tts(payload: TTSRequest) -> dict[str, str]:
    try:
        tool_result = pyttsx3_tts_tool.invoke(
            {
                "text": payload.text,
                "rate": payload.rate,
                "volume": payload.volume,
            }
        )
        data = json.loads(tool_result)
        if data.get("status") != "spoken":
            raise ValueError(f"Unexpected TTS tool result: {data}")
        return {"status": "spoken"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"TTS failed: {exc}") from exc
