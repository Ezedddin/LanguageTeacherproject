"""
Agent 3: Tutor Agent
Per-turn language tutor with:
  - RAG: retrieves relevant grammar rules from the knowledge base
  - Session memory: tracks difficulty, topics, accuracy across turns
  - Structured feedback: correctness + error explanation + follow-up exercise
  - Difficulty adaptation: after every 3 responses, adjusts level up/same/down
  - Session phases: warm_up → exercise (3-5 rounds) → summary

LangGraph graph per turn: load_memory → rag → generate → save_memory
Uses the OpenAI API with function calling for structured output.
"""

import json
import operator
import os
from typing import Annotated, Literal, Optional, TypedDict

from langgraph.graph import END, StateGraph
from openai import OpenAI
from pydantic import BaseModel, Field

from .assessment_agent import AssessmentResult
from .planning_agent import LearningPlan

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# ── Knowledge base (embedded; can be swapped for a vector store) ─────────────

_KNOWLEDGE_BASE = [
    {
        "topic": "verb to be (present)",
        "level": "A1",
        "content": "Use am/is/are to describe states. I am happy. She is tall. They are students.",
        "exercise": "Fill in the blank: She ___ (be) a teacher.",
    },
    {
        "topic": "present simple",
        "level": "A1",
        "content": "Use the base form for routines. Add -s/-es for he/she/it. I eat. He eats.",
        "exercise": "Translate: I wake up at 7am every day.",
    },
    {
        "topic": "common vocabulary – everyday objects",
        "level": "A1",
        "content": "house, table, chair, phone, book, water, food, school, work, time",
        "exercise": "Short answer: Name 5 objects you can see right now in English.",
    },
    {
        "topic": "past simple – regular verbs",
        "level": "A2",
        "content": "Add -ed for regular verbs in the past. I walked. She cooked. They played.",
        "exercise": "Fill in: Yesterday I ___ (walk) to school.",
    },
    {
        "topic": "past simple – irregular verbs",
        "level": "A2",
        "content": "Common irregulars: go→went, see→saw, eat→ate, have→had, do→did, say→said.",
        "exercise": "Correct the error: Last night I goed to the cinema.",
    },
    {
        "topic": "sentence connectors",
        "level": "A2",
        "content": "Use because (reason), but (contrast), so (result), and (addition) to link ideas.",
        "exercise": "Join these sentences: I was tired. I went to bed early.",
    },
    {
        "topic": "future with will / going to",
        "level": "A2",
        "content": "will = decisions made now / predictions. going to = plans already made.",
        "exercise": "Fill in: I ___ (go) to Paris next summer — I already booked the flight.",
    },
    {
        "topic": "present perfect",
        "level": "B1",
        "content": "Use have/has + past participle for experiences or recent results. I have never visited Paris.",
        "exercise": "Fill in: She ___ just ___ (finish) the report.",
    },
    {
        "topic": "giving opinions",
        "level": "B1",
        "content": "Phrases: In my opinion..., I think that..., I believe..., From my perspective...",
        "exercise": "Short answer: Give your opinion on learning languages online (3+ sentences).",
    },
    {
        "topic": "first conditional",
        "level": "B1",
        "content": "If + present simple → will + base form. For real/likely situations. If it rains, I will stay home.",
        "exercise": "Complete: If you study every day, you ___.",
    },
    {
        "topic": "passive voice",
        "level": "B2",
        "content": "Subject receives the action: be + past participle. The report was written by Ana.",
        "exercise": "Rewrite in passive: The chef prepared the meal.",
    },
    {
        "topic": "second conditional",
        "level": "B2",
        "content": "If + past simple → would + base form. For hypothetical situations. If I had more time, I would travel.",
        "exercise": "Complete: If I could live anywhere, I ___.",
    },
    {
        "topic": "modal verbs",
        "level": "B2",
        "content": "must (obligation), should (advice), could (past ability/possibility), might (weak possibility).",
        "exercise": "Rewrite: It is necessary for you to submit this form. (Use 'must'.)",
    },
    {
        "topic": "complex sentence structure",
        "level": "B2",
        "content": "Relative clauses: who/which/that. The person who helped me is my teacher.",
        "exercise": "Combine: I met a woman. She speaks six languages.",
    },
]


def _retrieve_knowledge(user_message: str, level: str) -> list[dict]:
    """Simple token-overlap retrieval filtered by CEFR level."""
    level_order = ["A1", "A2", "B1", "B2"]
    idx = level_order.index(level)
    eligible_levels = set(level_order[: idx + 2])

    tokens = set(user_message.lower().split())
    scored = []
    for item in _KNOWLEDGE_BASE:
        if item["level"] not in eligible_levels:
            continue
        topic_tokens = set(item["topic"].lower().split())
        score = len(tokens & topic_tokens)
        scored.append((score, item))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored[:3]]


# ── Pydantic models ──────────────────────────────────────────────────────────

class ExerciseFeedback(BaseModel):
    is_correct: bool
    explanation: str
    corrected_version: Optional[str] = None
    follow_up_exercise: str


class Exercise(BaseModel):
    type: Literal[
        "fill_in_the_blank",
        "translation",
        "short_answer",
        "conversation",
        "multiple_choice",
        "correction",
    ]
    prompt: str
    expected_answer: Optional[str] = None
    difficulty: Literal["easier", "same", "harder"]
    topic: str


class TutorResponse(BaseModel):
    message: str
    exercise: Optional[Exercise] = None
    feedback: Optional[ExerciseFeedback] = None
    session_complete: bool = False
    progress_note: str


class SessionMemory(BaseModel):
    responses_in_session: int = 0
    correct_in_last_3: int = 0
    total_in_last_3: int = 0
    current_difficulty: Literal["easier", "same", "harder"] = "same"
    recent_topics: list[str] = Field(default_factory=list)
    weak_areas: list[str] = Field(default_factory=list)
    progress_notes: list[str] = Field(default_factory=list)
    exercise_count: int = 0
    phase: Literal["warm_up", "exercise", "summary"] = "warm_up"


# ── Difficulty logic ─────────────────────────────────────────────────────────

def _compute_next_difficulty(
    correct: int, total: int, current: Literal["easier", "same", "harder"]
) -> Literal["easier", "same", "harder"]:
    if total < 3:
        return current
    accuracy = correct / total
    if accuracy >= 0.8:
        return "harder"
    if accuracy <= 0.4:
        return "easier"
    return "same"


# ── LangGraph state ──────────────────────────────────────────────────────────

class TutorState(TypedDict):
    assessment: dict
    plan: dict
    memory: dict
    conversation: Annotated[list[dict], operator.add]
    user_message: str
    rag_context: list[dict]
    lesson_context: dict | None   # designed lesson from Bot 4, optional
    response: dict | None
    exercise_history: Annotated[list[dict], operator.add]


# ── Graph nodes ──────────────────────────────────────────────────────────────

def _load_memory_node(state: TutorState) -> TutorState:
    return state


def _rag_node(state: TutorState) -> TutorState:
    level = state["assessment"].get("level", "A1")
    items = _retrieve_knowledge(state["user_message"], level)
    return {**state, "rag_context": items}


_TUTOR_FUNCTION = {
    "name": "tutor_response",
    "description": "Generate a structured tutor response with optional exercise and feedback.",
    "parameters": {
        "type": "object",
        "properties": {
            "message": {
                "type": "string",
                "description": "The tutor's conversational message to the learner.",
            },
            "exercise": {
                "type": "object",
                "description": "An exercise for the learner. Omit during warm_up phase.",
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": [
                            "fill_in_the_blank",
                            "translation",
                            "short_answer",
                            "conversation",
                            "multiple_choice",
                            "correction",
                        ],
                    },
                    "prompt": {"type": "string"},
                    "expected_answer": {
                        "type": "string",
                        "description": "The ideal answer. Omit for open-ended types.",
                    },
                    "difficulty": {"type": "string", "enum": ["easier", "same", "harder"]},
                    "topic": {"type": "string"},
                },
                "required": ["type", "prompt", "difficulty", "topic"],
            },
            "feedback": {
                "type": "object",
                "description": "Feedback on the learner's previous answer. Omit on first turn.",
                "properties": {
                    "is_correct": {"type": "boolean"},
                    "explanation": {
                        "type": "string",
                        "description": "Explain WHY it is right or wrong — the grammar rule, not just the fix.",
                    },
                    "corrected_version": {
                        "type": "string",
                        "description": "The corrected sentence. Omit if answer was correct.",
                    },
                    "follow_up_exercise": {
                        "type": "string",
                        "description": "A short exercise targeting the same error pattern.",
                    },
                },
                "required": ["is_correct", "explanation", "follow_up_exercise"],
            },
            "session_complete": {
                "type": "boolean",
                "description": "Set true only when the summary phase is done.",
            },
            "progress_note": {
                "type": "string",
                "description": "One sentence for the memory log about this turn.",
            },
        },
        "required": ["message", "session_complete", "progress_note"],
    },
}


def _format_lesson_context(lesson: dict) -> str:
    """Format the designed lesson into a readable context block for the system prompt."""
    lines = [
        f"DESIGNED LESSON: {lesson.get('title', '')}",
        f"Objective: {lesson.get('objective', '')}",
        f"Estimated time: {lesson.get('estimated_minutes', '?')} minutes",
        "Phases:",
    ]
    for phase in lesson.get("phases", []):
        name = phase.get("phase_name", "?")
        goal = phase.get("goal", "")
        lines.append(f"  [{name}] {goal}")

        vocab = phase.get("vocab_selection", [])
        if vocab:
            lines.append(f"    Vocabulary: {', '.join(vocab)}")

        tasks = phase.get("guided_tasks", [])
        if tasks:
            lines.append(f"    Tasks: {'; '.join(str(t) for t in tasks[:2])}")

        scenario = phase.get("scenario_prompt", "")
        if scenario:
            lines.append(f"    Scenario: {scenario}")

        tip = phase.get("expert_tip", "")
        if tip:
            lines.append(f"    Tip: {tip}")
    return "\n".join(lines)


def _generate_node(state: TutorState) -> TutorState:
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    memory = SessionMemory(**state["memory"])
    difficulty = _compute_next_difficulty(
        memory.correct_in_last_3, memory.total_in_last_3, memory.current_difficulty
    )

    rag_text = "\n".join(
        f"  - {item['topic']} ({item['level']}): {item['content']}"
        for item in state.get("rag_context", [])
    )

    # Determine current week focus from the 12-week plan
    week_num = min(1 + memory.exercise_count // 5, 12)
    weekly_goals = state["plan"].get("weekly_goals", [])
    current_week_goal = next(
        (g for g in weekly_goals if g["week"] == week_num),
        weekly_goals[0] if weekly_goals else {},
    )

    # Use lesson design from Bot 4 if available, otherwise fall back to weekly goal
    lesson_context = state.get("lesson_context")
    if lesson_context:
        lesson_block = _format_lesson_context(lesson_context)

        # Determine which phase to execute based on memory.exercise_count
        designed_phases = lesson_context.get("phases", [])
        phase_index = min(memory.exercise_count, len(designed_phases) - 1)
        current_designed_phase = designed_phases[phase_index] if designed_phases else {}
        current_phase_name = current_designed_phase.get("phase_name", memory.phase)
        current_phase_goal = current_designed_phase.get("goal", "")
        current_phase_tasks = current_designed_phase.get("guided_tasks", [])
        current_phase_vocab = current_designed_phase.get("vocab_selection", [])
        current_phase_scenario = current_designed_phase.get("scenario_prompt", "")

        phase_instruction = (
            f"LESSON PHASE: {current_phase_name} ({memory.exercise_count + 1}/{len(designed_phases)})\n"
            f"Phase goal: {current_phase_goal}\n"
            + (f"Vocabulary to cover: {', '.join(current_phase_vocab)}\n" if current_phase_vocab else "")
            + (f"Tasks to use: {'; '.join(str(t) for t in current_phase_tasks)}\n" if current_phase_tasks else "")
            + (f"Scenario: {current_phase_scenario}\n" if current_phase_scenario else "")
            + f"Difficulty: {difficulty}.\n"
            + ("If the learner just answered, give structured feedback first, then continue the phase." if memory.exercise_count > 0 else "")
            + ("\nSet session_complete=true after completing the final phase." if phase_index == len(designed_phases) - 1 else "")
        )
    else:
        lesson_block = ""
        phase_instruction = {
            "warm_up": (
                "WARM-UP PHASE: Greet the learner warmly. Ask them to recall one thing from a "
                "previous topic, or if this is their first session, explain what you'll work on today. "
                "Do NOT give an exercise yet."
            ),
            "exercise": (
                f"EXERCISE PHASE ({memory.exercise_count}/5 done): "
                f"This week's focus: {current_week_goal.get('topic', 'general practice')}. "
                f"Grammar focus: {current_week_goal.get('grammar_focus', 'general')}. "
                f"Current difficulty: {difficulty}. "
                f"If the learner just answered an exercise, provide feedback FIRST "
                f"(correctness + grammar rule explanation + follow-up). "
                f"Then give the next exercise of type: "
                f"{current_week_goal.get('exercise_types', ['short_answer'])[0]}."
            ),
            "summary": (
                "SUMMARY PHASE: The session is ending. Summarize: (1) what the learner did well, "
                "(2) the top 1-2 things to keep practicing, (3) one specific goal for next session. "
                "Set session_complete=true."
            ),
        }[memory.phase]

    recent = state.get("exercise_history", [])[-3:]
    history_text = ""
    if recent:
        history_text = "Last 3 exercises:\n" + "\n".join(
            f"  - {'correct' if e.get('was_correct') else 'incorrect'} "
            f"{e.get('type', '?')}: {e.get('prompt', '')[:60]}"
            for e in recent
        )

    system = (
        f"You are an adaptive English language tutor.\n\n"
        f"Learner profile:\n"
        f"  - CEFR level: {state['assessment']['level']}\n"
        f"  - Weak areas: {', '.join(state['assessment'].get('weak_areas', []))}\n"
        f"  - Strong areas: {', '.join(state['assessment'].get('strong_areas', []))}\n"
        f"  - Exercises completed this session: {memory.exercise_count}\n\n"
        + (f"Current lesson design:\n{lesson_block}\n\n" if lesson_block else "")
        + f"Relevant grammar knowledge:\n{rag_text or '  (none retrieved)'}\n\n"
        f"{history_text}\n\n"
        f"CURRENT INSTRUCTION:\n{phase_instruction}\n\n"
        f"FEEDBACK FORMAT (when evaluating a learner answer):\n"
        f"  1. State correctness clearly\n"
        f"  2. Explain the grammar rule behind the error — WHY it's wrong\n"
        f"  3. Give corrected_version if wrong\n"
        f"  4. Give a follow_up_exercise targeting the same error pattern\n\n"
        f"DIFFICULTY RULE: After every 3 responses → "
        f">=80% correct=harder, <=40%=easier, else=same. "
        f"Current setting: {difficulty}."
    )

    messages = (
        [{"role": "system", "content": system}]
        + state["conversation"]
        + [{"role": "user", "content": state["user_message"]}]
    )

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        tools=[{"type": "function", "function": _TUTOR_FUNCTION}],
        tool_choice={"type": "function", "function": {"name": "tutor_response"}},
        messages=messages,
    )

    tool_call = response.choices[0].message.tool_calls[0]
    return {**state, "response": json.loads(tool_call.function.arguments)}


def _save_memory_node(state: TutorState) -> TutorState:
    if not state.get("response"):
        return state

    memory = SessionMemory(**state["memory"])
    resp = state["response"]

    memory.responses_in_session += 1

    if resp.get("feedback"):
        was_correct = resp["feedback"]["is_correct"]
        memory.total_in_last_3 += 1
        if was_correct:
            memory.correct_in_last_3 += 1

        # Evaluate and reset after 3 responses
        if memory.total_in_last_3 >= 3:
            memory.current_difficulty = _compute_next_difficulty(
                memory.correct_in_last_3, memory.total_in_last_3, memory.current_difficulty
            )
            memory.correct_in_last_3 = 0
            memory.total_in_last_3 = 0

    if resp.get("exercise"):
        memory.exercise_count += 1
        topic = resp["exercise"].get("topic", "")
        if topic and topic not in memory.recent_topics:
            memory.recent_topics = ([topic] + memory.recent_topics)[:6]

    if resp.get("progress_note"):
        memory.progress_notes = ([resp["progress_note"]] + memory.progress_notes)[:10]

    # Advance phase
    if memory.phase == "warm_up":
        memory.phase = "exercise"
    elif memory.phase == "exercise" and memory.exercise_count >= 5:
        memory.phase = "summary"

    return {**state, "memory": memory.model_dump()}


def _create_tutor_graph():
    graph = StateGraph(TutorState)

    graph.add_node("load_memory", _load_memory_node)
    graph.add_node("rag", _rag_node)
    graph.add_node("generate", _generate_node)
    graph.add_node("save_memory", _save_memory_node)

    graph.set_entry_point("load_memory")
    graph.add_edge("load_memory", "rag")
    graph.add_edge("rag", "generate")
    graph.add_edge("generate", "save_memory")
    graph.add_edge("save_memory", END)

    return graph.compile()


_tutor_graph = _create_tutor_graph()


def run_tutor_turn(
    user_message: str,
    assessment: AssessmentResult,
    plan: LearningPlan,
    memory: SessionMemory,
    conversation: list[dict],
    exercise_history: list[dict],
    lesson_context: dict | None = None,
) -> tuple[TutorResponse, SessionMemory, list[dict], list[dict]]:
    """
    Run one turn of the tutor agent.
    lesson_context: the designed lesson dict from Bot 4 (optional).
                    When provided, the tutor follows the lesson's phases, vocabulary,
                    and guided tasks instead of the generic weekly goal.
    Returns: (response, updated_memory, updated_conversation, updated_exercise_history)
    """
    result = _tutor_graph.invoke(
        {
            "assessment": assessment.model_dump(),
            "plan": plan.model_dump(),
            "memory": memory.model_dump(),
            "conversation": conversation,
            "user_message": user_message,
            "rag_context": [],
            "lesson_context": lesson_context,
            "response": None,
            "exercise_history": exercise_history,
        }
    )

    resp_data = result["response"]
    new_memory = SessionMemory(**result["memory"])

    new_conversation = conversation + [
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": resp_data["message"]},
    ]

    new_history = list(exercise_history)
    if resp_data.get("exercise"):
        ex = resp_data["exercise"]
        new_history.append(
            {
                "type": ex.get("type"),
                "prompt": ex.get("prompt", ""),
                "topic": ex.get("topic", ""),
                "was_correct": None,
            }
        )
    if resp_data.get("feedback") and new_history:
        new_history[-1]["was_correct"] = resp_data["feedback"]["is_correct"]

    tutor_resp = TutorResponse(
        message=resp_data["message"],
        exercise=Exercise(**resp_data["exercise"]) if resp_data.get("exercise") else None,
        feedback=(
            ExerciseFeedback(**resp_data["feedback"]) if resp_data.get("feedback") else None
        ),
        session_complete=resp_data.get("session_complete", False),
        progress_note=resp_data.get("progress_note", ""),
    )

    return tutor_resp, new_memory, new_conversation, new_history
