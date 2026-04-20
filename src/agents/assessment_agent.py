"""
Agent 1: Assessment Agent
Collects 4 free-form language samples and returns a structured CEFR assessment
using the Google Gemini API with native Pydantic response_schema support.
"""

import json
import os
from typing import Literal

from google import genai
from google.genai import types
from openai import OpenAI
from pydantic import BaseModel, Field

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
OPENAI_ASSESSMENT_MODEL = os.getenv("OPENAI_ASSESSMENT_MODEL", "gpt-4.1-mini")

ASSESSMENT_PROMPTS = [
    "Tell me about yourself — your name, where you're from, and why you want to learn this language.",
    "Describe what you did yesterday from morning to evening.",
    "What do you think is the hardest part of learning a new language? Explain your opinion.",
    "Describe a place that is important to you and explain why it matters to you.",
]

CEFR_GUIDE = """
CEFR level guidelines:
- A1 (Beginner): Very basic phrases, single words, heavy errors, no sentence complexity.
- A2 (Elementary): Simple sentences, frequent errors, limited vocabulary, can express routine needs.
- B1 (Intermediate): Can handle most familiar situations, reasonable accuracy, some complex sentences.
- B2 (Upper-Intermediate): Fluent in most contexts, minor errors, good range of vocabulary and structure.
"""


class AssessmentResult(BaseModel):
    level: Literal["A1", "A2", "B1", "B2"]
    vocabulary_score: int = Field(ge=1, le=5)
    grammar_score: int = Field(ge=1, le=5)
    fluency_score: int = Field(ge=1, le=5)
    weak_areas: list[str]
    strong_areas: list[str]
    recommended_focus: str
    reasoning: str


def _stringify(value: object) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        parts = [str(item).strip() for item in value if str(item).strip()]
        return "; ".join(parts)
    if value is None:
        return ""
    return str(value).strip()


def _string_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        # Accept comma/semicolon/newline separated fallback formats.
        normalized = text.replace("\n", ",").replace(";", ",")
        return [part.strip() for part in normalized.split(",") if part.strip()]
    return []


def _normalize_assessment_payload(payload: dict) -> dict:
    def _score(value: object) -> int:
        try:
            parsed = int(value)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            parsed = 3
        return max(1, min(5, parsed))

    raw_level = _stringify(payload.get("level")).upper()
    normalized_level = "A1"
    for candidate in ("A1", "A2", "B1", "B2"):
        if candidate in raw_level:
            normalized_level = candidate
            break
    return {
        "level": normalized_level,
        "vocabulary_score": _score(payload.get("vocabulary_score", 3)),
        "grammar_score": _score(payload.get("grammar_score", 3)),
        "fluency_score": _score(payload.get("fluency_score", 3)),
        "weak_areas": _string_list(payload.get("weak_areas")),
        "strong_areas": _string_list(payload.get("strong_areas")),
        "recommended_focus": _stringify(payload.get("recommended_focus")),
        "reasoning": _stringify(payload.get("reasoning")),
    }


def _build_prompt(language_samples: list[str], target_language: str) -> str:
    combined_samples = "\n\n".join(
        f"Question {i + 1}: {ASSESSMENT_PROMPTS[i]}\n"
        f"Learner's answer: {sample}"
        for i, sample in enumerate(language_samples)
    )
    return (
        f"You are a certified {target_language} language assessment expert.\n"
        f"{CEFR_GUIDE}\n\n"
        f"Analyze the following learner responses carefully. "
        f"Look at vocabulary range, grammatical accuracy, sentence complexity, "
        f"and communication fluency.\n\n"
        f"{combined_samples}\n\n"
        f"Based on these responses, determine the learner's CEFR level and "
        f"return your structured assessment as JSON."
    )


def _run_gemini_assessment(prompt: str) -> AssessmentResult:
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=AssessmentResult,
            temperature=0.2,
        ),
    )
    parsed = json.loads(response.text or "{}")
    return AssessmentResult.model_validate(_normalize_assessment_payload(parsed))


def _run_openai_assessment(prompt: str) -> AssessmentResult:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required for OpenAI assessment fallback.")
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=OPENAI_ASSESSMENT_MODEL,
        temperature=0.2,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "Return only valid JSON matching this schema: "
                    "{level, vocabulary_score, grammar_score, fluency_score, "
                    "weak_areas, strong_areas, recommended_focus, reasoning}."
                ),
            },
            {"role": "user", "content": prompt},
        ],
    )
    payload = response.choices[0].message.content or "{}"
    return AssessmentResult.model_validate(
        _normalize_assessment_payload(json.loads(payload))
    )


def run_assessment(language_samples: list[str], target_language: str = "English") -> AssessmentResult:
    """
    Run the assessment agent on 4 language samples.
    Returns a structured AssessmentResult with CEFR level and scores.
    """
    if len(language_samples) != 4:
        raise ValueError(f"Expected 4 language samples, got {len(language_samples)}")

    prompt = _build_prompt(language_samples, target_language)
    try:
        return _run_gemini_assessment(prompt)
    except Exception as exc:
        message = str(exc).lower()
        if "resource_exhausted" in message or "quota" in message or "429" in message:
            return _run_openai_assessment(prompt)
        raise
