from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Literal

from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from pydantic import BaseModel, Field, ValidationError


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSESSMENT_DIR = PROJECT_ROOT / "Assesment-agent"
PLANNER_DIR = PROJECT_ROOT / "planner-agent"
for candidate in (PROJECT_ROOT, ASSESSMENT_DIR, PLANNER_DIR):
    value = str(candidate)
    if candidate.exists() and value not in sys.path:
        sys.path.append(value)

from assessment_agent import AssessmentResult  # noqa: E402
from planner_agent import LearningPlan  # noqa: E402


class VocabItem(BaseModel):
    term: str
    meaning: str
    example_sentence: str


class GuidedTask(BaseModel):
    prompt: str
    sentence_with_blank: str
    expected_answer: str
    hint: str


class LessonPhase(BaseModel):
    phase: Literal[
        "warm_up",
        "input",
        "guided_practice",
        "output_speaking",
        "feedback_correction",
    ]
    duration_minutes: int = Field(ge=5, le=20)
    goal: str
    teacher_actions: list[str] = Field(min_length=1, max_length=3)
    learner_actions: list[str] = Field(min_length=1, max_length=3)
    vocab_selection: list[VocabItem] = Field(default_factory=list, max_length=8)
    guided_tasks: list[GuidedTask] = Field(default_factory=list, max_length=3)
    scenario_prompt: str = ""
    expert_tip: str = ""


class DesignedLesson(BaseModel):
    lesson_id: str
    week: int = Field(ge=1, le=12)
    lesson_number: int = Field(ge=1, le=3)
    title: str
    objective: str
    estimated_minutes: int = Field(ge=35, le=75)
    phases: list[LessonPhase] = Field(min_length=5, max_length=5)


class CurriculumDesign(BaseModel):
    lessons: list[DesignedLesson]


class LessonDesignerAgent:
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        provider: str | None = None,
    ) -> None:
        requested_provider = (provider or os.getenv("LESSON_DESIGNER_PROVIDER", "openai")).lower()
        self.provider = requested_provider
        self.client: Any = None

        # Safe default: if OpenAI is requested but key is absent and Gemini key exists,
        # transparently fall back to Gemini so the pipeline stays available.
        if (
            self.provider == "openai"
            and not (api_key or os.getenv("OPENAI_API_KEY"))
            and os.getenv("GEMINI_API_KEY")
        ):
            self.provider = "gemini"

        if self.provider == "openai":
            try:
                from openai import OpenAI
            except ModuleNotFoundError as exc:
                raise ValueError(
                    "OpenAI SDK ontbreekt. Installeer dependency 'openai' in requirements."
                ) from exc
            self.model = model or os.getenv("LESSON_DESIGNER_MODEL", "gpt-4.1-mini")
            self.api_key = api_key or os.getenv("OPENAI_API_KEY")
            if not self.api_key:
                raise ValueError("Missing OPENAI_API_KEY. Set it in environment or pass api_key.")
            self.client = OpenAI(api_key=self.api_key)
            return

        if self.provider == "gemini":
            self.model = model or os.getenv("LESSON_DESIGNER_MODEL", "gemini-2.5-flash")
            self.api_key = api_key or os.getenv("GEMINI_API_KEY")
            if not self.api_key:
                raise ValueError("Missing GEMINI_API_KEY. Set it in environment or pass api_key.")
            self.client = genai.Client(api_key=self.api_key)
            return

        raise ValueError(
            f"Unsupported LESSON_DESIGNER_PROVIDER '{self.provider}'. Use 'openai' or 'gemini'."
        )

    def _build_prompt(
        self,
        assessment: AssessmentResult,
        plan: LearningPlan,
        lessons_per_week: int,
        target_language: str = "English",
    ) -> str:
        return f"""
You are a lesson designer for a language learning app.
Create detailed, structured lessons from this 12-week plan.

Assessment:
- Level: {assessment.level}
- Weak areas: {", ".join(assessment.weak_areas)}
- Strong areas: {", ".join(assessment.strong_areas)}
- Recommended focus: {assessment.recommended_focus}

Plan:
- Target language: {target_language}
- Duration weeks: {plan.duration_weeks}
- Weekly goals: {json.dumps([goal.model_dump() for goal in plan.weekly_goals], ensure_ascii=True)}
- Priority skills: {", ".join(plan.priority_skills)}
- Summary: {plan.summary}

Requirements:
- Generate exactly {lessons_per_week} lessons per week, for all 12 weeks.
- lesson_id format: W{{week}}-L{{lesson_number}}
- Each lesson must have exactly 5 phases in this order:
  1) warm_up
  2) input
  3) guided_practice
  4) output_speaking
  5) feedback_correction
- Input phase: include exactly 5 new vocabulary items (term, meaning, example_sentence).
- Guided_practice phase: include exactly 3 guided tasks.
- Output phase: include a realistic scenario prompt.
- Avoid repeating the same vocabulary across lessons.
- Keep content practical and CEFR-appropriate.
- Strong pedagogy constraint: prioritize sentence-building over isolated word drills.
- Vocabulary style: use beginner-friendly words (early classroom / daycare level) in the first lessons.
- Every guided task must require producing or completing a full short sentence.
- Example sentences must be very short, clear, and usable in daily life.
- Prefer high-frequency foundations first: greetings, family, colors, numbers, classroom objects, food, emotions, routines.
""".strip()

    def _normalize_payload(
        self,
        payload: dict,
        target_language: str = "English",
    ) -> CurriculumDesign:
        raw_lessons = payload.get("lessons", [])
        if not isinstance(raw_lessons, list):
            raise ValueError("Lesson designer payload must contain a lessons array.")

        lessons: list[DesignedLesson] = []
        for item in raw_lessons:
            if not isinstance(item, dict):
                raise ValueError("Each lesson must be an object.")
            normalized_item = self._normalize_lesson_shape(item, target_language=target_language)
            lesson = DesignedLesson.model_validate(normalized_item)
            phase_order = [p.phase for p in lesson.phases]
            required_order = [
                "warm_up",
                "input",
                "guided_practice",
                "output_speaking",
                "feedback_correction",
            ]
            if phase_order != required_order:
                raise ValueError(
                    f"Invalid phase order in {lesson.lesson_id}: {phase_order}"
                )
            input_phase = next(p for p in lesson.phases if p.phase == "input")
            guided_phase = next(p for p in lesson.phases if p.phase == "guided_practice")
            if len(input_phase.vocab_selection) != 5:
                raise ValueError(
                    f"{lesson.lesson_id} must include exactly 5 vocab items in input phase."
                )
            if len(guided_phase.guided_tasks) != 3:
                raise ValueError(
                    f"{lesson.lesson_id} must include exactly 3 guided tasks."
                )
            lessons.append(lesson)

        if not lessons:
            raise ValueError("Lesson designer returned no lessons.")
        return CurriculumDesign(lessons=lessons)

    def _text_or_empty(self, value: object) -> str:
        if value is None:
            return ""
        return str(value).strip()

    def _normalize_guided_task(self, task: object) -> dict:
        if isinstance(task, str):
            text = self._text_or_empty(task)
            if not text:
                raise ValueError("Guided task string cannot be empty.")
            return {
                "prompt": text,
                "sentence_with_blank": text,
                "expected_answer": "Write one short beginner sentence in the target language.",
                "hint": "Use one of the 5 lesson words inside a full sentence.",
            }
        if not isinstance(task, dict):
            raise ValueError("Guided task must be an object.")
        examples_raw = task.get("examples", [])
        examples = examples_raw if isinstance(examples_raw, list) else []
        single_example = self._text_or_empty(task.get("example"))
        if single_example:
            examples = [single_example, *examples]
        first_example = ""
        for example in examples:
            text = self._text_or_empty(example)
            if text:
                first_example = text
                break
        prompt = self._text_or_empty(
            task.get("prompt")
            or task.get("question")
            or task.get("instruction")
            or task.get("instructions")
            or task.get("task")
        )
        sentence = self._text_or_empty(
            task.get("sentence_with_blank")
            or task.get("sentence")
            or task.get("text")
            or task.get("question")
            or task.get("prompt")
            or task.get("instructions")
            or first_example
        )
        expected = self._text_or_empty(
            task.get("expected_answer")
            or task.get("answer")
            or task.get("correct_answer")
            or task.get("example_answer")
            or task.get("model_answer")
            or first_example
        )
        hint = self._text_or_empty(task.get("hint") or task.get("clue") or task.get("support"))
        if not prompt or not sentence or not expected:
            raise ValueError(f"Guided task missing required meaning-bearing fields: {task}")
        if expected.lower() in {"provide a correct response.", "correct response", "correct answer"}:
            expected = "Write one short beginner sentence in the target language."
        if not hint:
            hint = "Use one of the 5 lesson words and answer with a short complete sentence."
        return {
            "prompt": prompt,
            "sentence_with_blank": sentence,
            "expected_answer": expected,
            "hint": hint,
        }

    def _normalize_phase_shape(self, phase: object) -> dict:
        if not isinstance(phase, dict):
            raise ValueError("Phase must be an object.")
        vocab = phase.get("vocab_selection", [])
        if not isinstance(vocab, list):
            vocab = []
        guided = phase.get("guided_tasks", [])
        if not isinstance(guided, list):
            guided = []
        normalized_guided = [self._normalize_guided_task(task) for task in guided]
        return {
            **phase,
            "vocab_selection": vocab,
            "guided_tasks": normalized_guided,
        }

    def _normalize_lesson_shape(self, lesson: dict, target_language: str) -> dict:
        phases = lesson.get("phases", [])
        if not isinstance(phases, list):
            raise ValueError("Lesson must contain phases as a list.")
        normalized_phases = [self._normalize_phase_shape(phase) for phase in phases]
        return {
            **lesson,
            "phases": normalized_phases,
        }

    def _extract_json_text(self, raw: str) -> str:
        text = raw.strip()
        if text.startswith("```"):
            text = text[3:]
            newline = text.find("\n")
            if newline != -1:
                text = text[newline:].strip()
            if text.endswith("```"):
                text = text[:-3].strip()
        return text

    def _build_retry_prompt(self, prompt: str, error_message: str) -> str:
        return (
            prompt
            + "\n\nYour previous output was invalid for schema validation."
            + f"\nValidation error: {error_message}"
            + "\nRegenerate the full curriculum from scratch."
            + "\nReturn JSON only, with strict adherence to:"
            + "\n- Exact phase order."
            + "\n- Exactly 5 vocabulary items in each input phase."
            + "\n- Exactly 3 guided tasks in each guided_practice phase."
        )

    def _design_with_openai(self, prompt: str, target_language: str = "English") -> CurriculumDesign:
        shape_hint = (
            prompt
            + "\n\nReturn valid JSON only with shape:\n"
            + '{"lessons":[{"lesson_id":"W1-L1","week":1,"lesson_number":1,"title":"...","objective":"...",'
            + '"estimated_minutes":50,"phases":[{"phase":"warm_up","duration_minutes":8,"goal":"...",'
            + '"teacher_actions":["..."],"learner_actions":["..."],"vocab_selection":[],'
            + '"guided_tasks":[],"scenario_prompt":"","expert_tip":""}]}]}'
        )
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0.35,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a curriculum lesson designer. "
                        "Return only valid JSON that matches the required shape."
                    ),
                },
                {"role": "user", "content": shape_hint},
            ],
        )
        text = response.choices[0].message.content or ""
        cleaned = self._extract_json_text(text)
        payload = json.loads(cleaned)
        return self._normalize_payload(payload, target_language=target_language)

    def _design_with_gemini(self, prompt: str, target_language: str = "English") -> CurriculumDesign:
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.35,
                response_mime_type="application/json",
                response_schema=CurriculumDesign,
            ),
        )
        parsed = getattr(response, "parsed", None)
        if isinstance(parsed, CurriculumDesign):
            return parsed
        if isinstance(parsed, dict):
            return self._normalize_payload(parsed, target_language=target_language)
        text = getattr(response, "text", None)
        if not text:
            raise ValueError("Lesson designer returned no parsed payload or text.")
        return self._normalize_payload(json.loads(text), target_language=target_language)

    def design_curriculum(
        self,
        assessment: AssessmentResult,
        plan: LearningPlan,
        lessons_per_week: int = 3,
        target_language: str = "English",
    ) -> CurriculumDesign:
        prompt = self._build_prompt(
            assessment=assessment,
            plan=plan,
            lessons_per_week=lessons_per_week,
            target_language=target_language,
        )
        if self.provider == "openai":
            try:
                return self._design_with_openai(prompt, target_language=target_language)
            except Exception as exc:
                retry_prompt = self._build_retry_prompt(prompt, str(exc))
                return self._design_with_openai(retry_prompt, target_language=target_language)

        try:
            return self._design_with_gemini(prompt, target_language=target_language)
        except genai_errors.ClientError as exc:
            # Gemini can reject large/complex schemas (400 INVALID_ARGUMENT).
            # Retry with relaxed schema, still fully AI-generated.
            if getattr(exc, "status_code", None) != 400:
                raise
            relaxed_prompt = (
                prompt
                + "\n\nReturn valid JSON only with shape:\n"
                + '{"lessons":[{"lesson_id":"W1-L1","week":1,"lesson_number":1,"title":"...","objective":"...",'
                + '"estimated_minutes":50,"phases":[{"phase":"warm_up","duration_minutes":8,"goal":"...",'
                + '"teacher_actions":["..."],"learner_actions":["..."],"vocab_selection":[],'
                + '"guided_tasks":[],"scenario_prompt":"","expert_tip":""}]}]}'
            )
            response = self.client.models.generate_content(
                model=self.model,
                contents=relaxed_prompt,
                config=types.GenerateContentConfig(
                    temperature=0.35,
                    response_mime_type="application/json",
                ),
            )
            text = getattr(response, "text", None)
            if not text:
                raise ValueError("Lesson designer fallback returned no text.")
            try:
                payload = json.loads(text)
            except json.JSONDecodeError as json_exc:
                raise ValueError(f"Lesson designer fallback returned invalid JSON: {text}") from json_exc
            try:
                return self._normalize_payload(payload, target_language=target_language)
            except Exception as normalize_exc:
                retry_prompt = self._build_retry_prompt(relaxed_prompt, str(normalize_exc))
                retry_response = self.client.models.generate_content(
                    model=self.model,
                    contents=retry_prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.2,
                        response_mime_type="application/json",
                    ),
                )
                retry_text = getattr(retry_response, "text", None)
                if not retry_text:
                    raise ValueError("Lesson designer retry returned no text.")
                retry_payload = json.loads(retry_text)
                return self._normalize_payload(retry_payload, target_language=target_language)
        except Exception as exc:
            retry_prompt = self._build_retry_prompt(prompt, str(exc))
            return self._design_with_gemini(retry_prompt, target_language=target_language)
