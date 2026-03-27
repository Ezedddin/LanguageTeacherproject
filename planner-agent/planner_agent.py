"""
Agent 2: Planning agent — genereert een persoonlijk leerplan op basis van AssessmentResult.
Gebruikt LangGraph conditional routing + Pydantic output.
"""
# pyright: reportMissingImports=false

from __future__ import annotations
import json
import os
import sys
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, Field, ValidationError, model_validator
from google import genai
from google.genai import types

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSESSMENT_DIR = PROJECT_ROOT / "Assesment-agent"
for candidate in (PROJECT_ROOT, ASSESSMENT_DIR):
    candidate_str = str(candidate)
    if candidate.exists() and candidate_str not in sys.path:
        sys.path.append(candidate_str)

from assessment_agent import AssessmentResult  # jouw Bot 1 output


# --- Output model voor Bot 2 ---

class WeeklyGoal(BaseModel):
    week: int = Field(ge=1, le=4)
    focus: str
    exercises: list[str] = Field(min_length=2, max_length=3)

class LearningPlan(BaseModel):
    level: Literal["A1", "A2", "B1", "B2"]
    target_level: Literal["A1", "A2", "B1", "B2"]
    duration_weeks: int = Field(ge=4, le=4)
    weekly_goals: list[WeeklyGoal] = Field(min_length=4, max_length=4)
    priority_skills: list[str]
    summary: str

    @model_validator(mode="after")
    def validate_level_progression_and_weeks(self) -> "LearningPlan":
        order = {"A1": 1, "A2": 2, "B1": 3, "B2": 4}
        if order[self.target_level] < order[self.level]:
            raise ValueError("target_level must be >= level")

        week_numbers = sorted(goal.week for goal in self.weekly_goals)
        if week_numbers != [1, 2, 3, 4]:
            raise ValueError("weekly_goals must contain week numbers 1..4 exactly once")

        return self


# --- LangGraph state ---

from typing import TypedDict

class AgentState(TypedDict):
    assessment: AssessmentResult
    route: Literal["beginner", "elementary", "intermediate", "upper_intermediate"] | None
    plan: LearningPlan | None


# --- Planning Agent ---

class PlanningAgent:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Missing GEMINI_API_KEY. Set it in environment or pass api_key.")
        self.client = genai.Client(api_key=self.api_key)

    @staticmethod
    def route_by_level(level: str) -> Literal["beginner", "elementary", "intermediate", "upper_intermediate"]:
        """Conditional routing: bepaal aanpak op basis van niveau."""
        return {
            "A1": "beginner",
            "A2": "elementary",
            "B1": "intermediate",
            "B2": "upper_intermediate",
        }[level]

    def _build_prompt(
        self,
        assessment: AssessmentResult,
        route: Literal["beginner", "elementary", "intermediate", "upper_intermediate"] | None = None,
    ) -> str:
        resolved_route = route or self.route_by_level(assessment.level)
        return f"""
You are a language learning planner for a {resolved_route} learner (CEFR level {assessment.level}).

Assessment summary:
- Weak areas: {', '.join(assessment.weak_areas)}
- Strong areas: {', '.join(assessment.strong_areas)}
- Recommended focus: {assessment.recommended_focus}
- Vocabulary score: {assessment.vocabulary_score}/5
- Grammar score: {assessment.grammar_score}/5
- Fluency score: {assessment.fluency_score}/5

Create a personalized learning plan for exactly 4 weeks that targets the weak areas.
Return strict JSON matching the schema with:
- duration_weeks = 4
- weekly_goals has exactly 4 items
- week values exactly 1,2,3,4
- each week has 2-3 concrete exercises
- target_level must be equal or higher than current level
""".strip()

    def create_plan(
        self,
        assessment: AssessmentResult,
        route: Literal["beginner", "elementary", "intermediate", "upper_intermediate"] | None = None,
    ) -> LearningPlan:
        prompt = self._build_prompt(assessment, route=route)
        response = self.client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                response_mime_type="application/json",
                response_schema=LearningPlan,
            ),
        )
        parsed = getattr(response, "parsed", None)
        if isinstance(parsed, LearningPlan):
            return parsed
        if isinstance(parsed, dict):
            return LearningPlan.model_validate(parsed)

        text = getattr(response, "text", None)
        if not text:
            raise ValueError("Planner model returned no parsed payload or text.")

        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Planner returned invalid JSON: {text}") from exc

        try:
            return LearningPlan.model_validate(data)
        except ValidationError as exc:
            raise ValueError(f"Planner response did not match LearningPlan schema: {data}") from exc


# --- LangGraph graph ---

from langgraph.graph import StateGraph, END

def assessment_node(state: AgentState) -> AgentState:
    """Bot 1 output zit al in de state; kies hier de route."""
    route = PlanningAgent.route_by_level(state["assessment"].level)
    return {**state, "route": route}

def route_selector(state: AgentState) -> str:
    return state["route"] or "beginner"

def planning_node(state: AgentState, forced_route: Literal["beginner", "elementary", "intermediate", "upper_intermediate"]) -> AgentState:
    agent = PlanningAgent()
    plan = agent.create_plan(state["assessment"], route=forced_route)
    return {**state, "plan": plan}

def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("assessment", assessment_node)
    graph.add_node(
        "planning_beginner",
        lambda state: planning_node(state, "beginner"),
    )
    graph.add_node(
        "planning_elementary",
        lambda state: planning_node(state, "elementary"),
    )
    graph.add_node(
        "planning_intermediate",
        lambda state: planning_node(state, "intermediate"),
    )
    graph.add_node(
        "planning_upper_intermediate",
        lambda state: planning_node(state, "upper_intermediate"),
    )
    graph.set_entry_point("assessment")
    graph.add_conditional_edges(
        "assessment",
        route_selector,
        {
            "beginner": "planning_beginner",
            "elementary": "planning_elementary",
            "intermediate": "planning_intermediate",
            "upper_intermediate": "planning_upper_intermediate",
        },
    )
    graph.add_edge("planning_beginner", END)
    graph.add_edge("planning_elementary", END)
    graph.add_edge("planning_intermediate", END)
    graph.add_edge("planning_upper_intermediate", END)
    return graph.compile()


# --- Test ---

if __name__ == "__main__":
    from assessment_agent import AssessmentAgent

    # Stap 1: Bot 1 uitvoeren
    agent1 = AssessmentAgent()
    result = agent1.assess(
        answer1="Hello, my name is Sofia.",
        answer2="I am from Spain, but now I live in Berlin.",
        answer3="I like reading books and playing volleyball.",
        answer4="Today I worked and cooked dinner.",
    )

    # Stap 2: Bot 2 uitvoeren via LangGraph
    app = build_graph()
    output = app.invoke({"assessment": result, "route": None, "plan": None})
    print(output["plan"].model_dump_json(indent=2))