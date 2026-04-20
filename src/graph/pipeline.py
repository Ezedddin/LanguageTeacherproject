"""
Full LangGraph pipeline that wires all three agents together.

  START → assessment_node → planning_node → END

The pipeline is used for the one-shot setup phase (assessment + planning).
The tutor agent runs separately on each user turn (see tutor_agent.run_tutor_turn).
"""

from typing import TypedDict

from langgraph.graph import END, StateGraph

from ..agents.assessment_agent import AssessmentResult, run_assessment
from ..agents.planning_agent import LearningPlan, run_planning


class PipelineState(TypedDict):
    # Inputs
    language_samples: list[str]
    target_language: str

    # Outputs populated by nodes
    assessment_result: dict | None
    learning_plan: dict | None


def _assessment_node(state: PipelineState) -> PipelineState:
    result: AssessmentResult = run_assessment(
        state["language_samples"], state["target_language"]
    )
    return {**state, "assessment_result": result.model_dump()}


def _planning_node(state: PipelineState) -> PipelineState:
    assessment = AssessmentResult(**state["assessment_result"])
    plan: LearningPlan = run_planning(assessment)
    return {**state, "learning_plan": plan.model_dump()}


def _create_pipeline():
    graph = StateGraph(PipelineState)

    graph.add_node("assessment", _assessment_node)
    graph.add_node("planning", _planning_node)

    graph.set_entry_point("assessment")
    graph.add_edge("assessment", "planning")
    graph.add_edge("planning", END)

    return graph.compile()


# Compiled pipeline — import and call .invoke() directly.
setup_pipeline = _create_pipeline()


def run_setup(language_samples: list[str], target_language: str = "English") -> PipelineState:
    """
    Run the full setup pipeline.
    Returns a PipelineState dict with assessment_result and learning_plan populated.
    """
    return setup_pipeline.invoke(
        {
            "language_samples": language_samples,
            "target_language": target_language,
            "assessment_result": None,
            "learning_plan": None,
        }
    )
