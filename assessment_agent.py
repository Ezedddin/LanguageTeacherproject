"""
Agent 1: CEFR assessment agent using Gemini + Pydantic structured output.

Requirements:
    pip install google-genai pydantic
"""

from __future__ import annotations

import json
import os
from typing import Literal

from pydantic import BaseModel, Field, ValidationError

try:
    from google import genai
    from google.genai import types
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "google-genai is not installed. Run: pip install google-genai"
    ) from exc


DEFAULT_SYSTEM_PROMPT = """
You are a CEFR language assessor.
Evaluate the user's language level based on their answers.
Pay attention to: vocabulary, grammatical complexity, sentence length and errors.
Always return a structured output.
""".strip()


class AssessmentResult(BaseModel):
    level: Literal["A1", "A2", "B1", "B2"] = Field(
        description="The CEFR level of the user"
    )
    reasoning: str = Field(
        min_length=10,
        max_length=500,
        description="Brief explanation of why this level was assigned",
    )
    vocabulary_score: int = Field(
        ge=1,
        le=5,
        description="Score for vocabulary range and accuracy (1=very limited, 5=varied and accurate)",
    )
    grammar_score: int = Field(
        ge=1,
        le=5,
        description="Score for grammatical complexity and correctness (1=many errors, 5=mostly correct)",
    )
    fluency_score: int = Field(
        ge=1,
        le=5,
        description="Score for sentence length and natural flow (1=very short/broken, 5=natural and fluid)",
    )
    weak_areas: list[str] = Field(
        min_length=1,
        max_length=5,
        description="List of specific weak points, e.g. ['verb conjugation', 'articles', 'word order']",
    )
    strong_areas: list[str] = Field(
        min_length=1,
        max_length=5,
        description="List of things the user already does well",
    )
    recommended_focus: str = Field(
        min_length=10,
        max_length=250,
        description="One sentence summarizing what the learning plan should focus on",
    )


class AssessmentAgent:
    """Gemini-based CEFR assessment agent."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gemini-2.5-flash-lite",
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
        temperature: float = 0.2,
    ) -> None:
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Missing Gemini API key. Set GEMINI_API_KEY or pass api_key."
            )

        self.model = model
        self.system_prompt = system_prompt
        self.temperature = temperature
        self.client = genai.Client(api_key=self.api_key)

    def _build_user_input(
        self,
        answer1: str,
        answer2: str,
        answer3: str,
        answer4: str,
    ) -> str:
        return f"""
Here are the user's answers in the language they are learning:

Question 1 (name): {answer1}
Question 2 (origin): {answer2}
Question 3 (hobbies): {answer3}
Question 4 (today): {answer4}

Determine the CEFR level.
""".strip()

    def _parse_response(self, response: object) -> AssessmentResult:
        # Best case: SDK already parsed according to response_schema.
        parsed = getattr(response, "parsed", None)
        if isinstance(parsed, AssessmentResult):
            return parsed
        if isinstance(parsed, dict):
            return AssessmentResult.model_validate(parsed)

        # Fallback: parse JSON from text.
        text = getattr(response, "text", None)
        if not text:
            raise ValueError("Gemini response has no parsed payload or text.")

        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON returned by model: {text}") from exc

        try:
            return AssessmentResult.model_validate(data)
        except ValidationError as exc:
            raise ValueError(f"Response did not match AssessmentResult schema: {data}") from exc

    def assess(
        self,
        answer1: str,
        answer2: str,
        answer3: str,
        answer4: str,
    ) -> AssessmentResult:
        user_input = self._build_user_input(answer1, answer2, answer3, answer4)

        response = self.client.models.generate_content(
            model=self.model,
            contents=user_input,
            config=types.GenerateContentConfig(
                system_instruction=self.system_prompt,
                temperature=self.temperature,
                response_mime_type="application/json",
                response_schema=AssessmentResult,
            ),
        )

        return self._parse_response(response)


def assess_language_level(
    answer1: str,
    answer2: str,
    answer3: str,
    answer4: str,
    api_key: str | None = None,
    model: str = "gemini-2.5-flash-lite",
) -> AssessmentResult:
    """
    Convenience function for quick CEFR assessment.
    """
    agent = AssessmentAgent(api_key=api_key, model=model)
    return agent.assess(answer1, answer2, answer3, answer4)


if __name__ == "__main__":
    demo_result = assess_language_level(
        answer1="Hello, my name is Sofia.",
        answer2="I am from Spain, but now I live in Berlin.",
        answer3="I like reading books and playing volleyball with my friends.",
        answer4="Today I worked, then I cooked dinner and watched a movie.",
    )
    print(demo_result.model_dump_json(indent=2))
