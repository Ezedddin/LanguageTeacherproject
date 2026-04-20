"""
Agent 2: Planning Agent
Takes an AssessmentResult and produces a structured 12-week learning plan.
Uses LangGraph for conditional routing based on CEFR level so each level
gets a prompt tuned to its appropriate pace and exercise mix.
Uses the OpenAI API with function calling for structured output.
"""

import json
import os
from typing import Literal, TypedDict

from langgraph.graph import END, StateGraph
from openai import OpenAI
from pydantic import BaseModel, Field, model_validator

from .assessment_agent import AssessmentResult

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

EXERCISE_TYPES = [
    "fill_in_the_blank",
    "translation",
    "short_answer",
    "conversation",
    "multiple_choice",
    "correction",
]

LEVEL_DESCRIPTIONS = {
    "A1": "beginner (just starting out, needs very simple vocabulary and present-tense exercises)",
    "A2": "elementary (knows basics, ready for past/future tense and simple connectors)",
    "B1": "intermediate (can handle most situations, needs work on complex tenses and opinion expression)",
    "B2": "upper-intermediate (fluent in most contexts, needs fine-tuning of nuance and complex structures)",
}

NEXT_LEVEL = {"A1": "A2", "A2": "B1", "B1": "B2", "B2": "B2"}

_PLAN_FUNCTION = {
    "name": "submit_learning_plan",
    "description": "Submit a structured 12-week personalized language learning plan.",
    "parameters": {
        "type": "object",
        "properties": {
            "level": {"type": "string", "enum": ["A1", "A2", "B1", "B2"]},
            "target_level": {"type": "string", "enum": ["A1", "A2", "B1", "B2"]},
            "duration_weeks": {"type": "integer"},
            "priority_skills": {
                "type": "array",
                "items": {"type": "string"},
                "description": "3-5 highest-priority skills to develop.",
            },
            "weekly_goals": {
                "type": "array",
                "description": "Exactly 12 weekly goals, one per week.",
                "items": {
                    "type": "object",
                    "properties": {
                        "week": {"type": "integer"},
                        "topic": {"type": "string"},
                        "exercise_types": {"type": "array", "items": {"type": "string"}},
                        "grammar_focus": {"type": "string"},
                        "vocabulary_theme": {"type": "string"},
                    },
                    "required": ["week", "topic", "exercise_types", "grammar_focus", "vocabulary_theme"],
                },
            },
            "summary": {
                "type": "string",
                "description": "2-3 sentence overview of the learning plan.",
            },
        },
        "required": ["level", "target_level", "duration_weeks", "priority_skills", "weekly_goals", "summary"],
    },
}


class WeeklyGoal(BaseModel):
    week: int = Field(ge=1, le=12)
    topic: str
    exercise_types: list[str]
    grammar_focus: str
    vocabulary_theme: str


class LearningPlan(BaseModel):
    level: Literal["A1", "A2", "B1", "B2"]
    target_level: Literal["A1", "A2", "B1", "B2"]
    duration_weeks: int = 12
    priority_skills: list[str]
    weekly_goals: list[WeeklyGoal]
    summary: str

    @model_validator(mode="after")
    def validate_plan(self) -> "LearningPlan":
        level_order = ["A1", "A2", "B1", "B2"]
        assert level_order.index(self.target_level) >= level_order.index(self.level), (
            "target_level must be >= current level"
        )
        assert len(self.weekly_goals) == 12, (
            f"Expected 12 weekly goals, got {len(self.weekly_goals)}"
        )
        return self


# ── LangGraph state ──────────────────────────────────────────────────────────

class PlanningState(TypedDict):
    assessment: dict
    target_language: str
    route: str
    plan: dict | None


def _route_selector(state: PlanningState) -> PlanningState:
    level = state["assessment"]["level"]
    routes = {
        "A1": "beginner",
        "A2": "elementary",
        "B1": "intermediate",
        "B2": "upper_intermediate",
    }
    return {**state, "route": routes[level]}


def _route_condition(state: PlanningState) -> str:
    return state["route"]


def _make_planning_node(route_label: str):
    def node(state: PlanningState) -> PlanningState:
        assessment = state["assessment"]
        target_language = state["target_language"]
        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        level = assessment["level"]
        target = NEXT_LEVEL[level]
        level_desc = LEVEL_DESCRIPTIONS[level]

        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            tools=[{"type": "function", "function": _PLAN_FUNCTION}],
            tool_choice={"type": "function", "function": {"name": "submit_learning_plan"}},
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Create a 12-week {target_language} learning plan for a {level_desc} learner.\n\n"
                        f"Learner profile:\n"
                        f"- Current level: {level}\n"
                        f"- Target level: {target}\n"
                        f"- Weak areas: {', '.join(assessment['weak_areas'])}\n"
                        f"- Strong areas: {', '.join(assessment['strong_areas'])}\n"
                        f"- Recommended focus: {assessment['recommended_focus']}\n\n"
                        f"Requirements:\n"
                        f"- Exactly 12 weekly goals (weeks 1 through 12)\n"
                        f"- Each week: topic, 2-3 exercise types from {EXERCISE_TYPES}, "
                        f"a grammar focus, and a vocabulary theme\n"
                        f"- Progress logically: weeks 1-4 build foundations, "
                        f"weeks 5-8 expand, weeks 9-12 consolidate and advance\n"
                        f"- Address the weak areas ({', '.join(assessment['weak_areas'])}) early in the plan"
                    ),
                }
            ],
        )

        tool_call = response.choices[0].message.tool_calls[0]
        return {**state, "plan": json.loads(tool_call.function.arguments)}

    node.__name__ = route_label
    return node


def _create_planning_graph():
    graph = StateGraph(PlanningState)

    graph.add_node("route_selector", _route_selector)
    for label in ["beginner", "elementary", "intermediate", "upper_intermediate"]:
        graph.add_node(label, _make_planning_node(label))
        graph.add_edge(label, END)

    graph.set_entry_point("route_selector")
    graph.add_conditional_edges(
        "route_selector",
        _route_condition,
        {
            "beginner": "beginner",
            "elementary": "elementary",
            "intermediate": "intermediate",
            "upper_intermediate": "upper_intermediate",
        },
    )
    return graph.compile()


_planning_graph = _create_planning_graph()


def run_planning(assessment: AssessmentResult, target_language: str = "English") -> LearningPlan:
    """Run the planning agent and return a validated 12-week LearningPlan."""
    result = _planning_graph.invoke(
        {
            "assessment": assessment.model_dump(),
            "target_language": target_language,
            "route": "",
            "plan": None,
        }
    )
    return LearningPlan(**result["plan"])
