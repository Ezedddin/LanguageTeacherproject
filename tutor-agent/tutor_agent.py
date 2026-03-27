"""
Bot 3: Tutor agent with LangGraph + RAG + session memory.

Architecture:
- Input from Bot 1 (AssessmentResult) and Bot 2 (LearningPlan)
- RAG retrieval from local knowledge base
- Session memory load/update
- LLM response generation with structured output
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Literal, TypedDict

from google import genai
from google.genai import types
from langgraph.graph import END, StateGraph
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


KB_PATH = Path(__file__).resolve().parent / "knowledge_base.json"
MEMORY_PATH = Path(__file__).resolve().parent / "session_memory.json"


class KnowledgeItem(BaseModel):
    id: str
    topic: str
    level: Literal["A1", "A2", "B1", "B2"]
    content: str
    exercise: str


class SessionMemory(BaseModel):
    user_id: str
    session_id: str
    recent_topics: list[str] = Field(default_factory=list)
    known_weak_areas: list[str] = Field(default_factory=list)
    known_strong_areas: list[str] = Field(default_factory=list)
    last_difficulty: Literal["easier", "same", "harder"] = "same"
    progress_notes: list[str] = Field(default_factory=list)


class TutorOutput(BaseModel):
    tutor_message: str = Field(
        description="What the tutor says to the learner right now."
    )
    suggested_exercise: str = Field(
        description="One concrete next exercise for the learner."
    )
    focus_topic: str = Field(description="Main topic this turn focuses on.")
    difficulty_adjustment: Literal["easier", "same", "harder"] = Field(
        description="How next step should adapt difficulty."
    )
    memory_note: str = Field(
        description="Short note to store in session memory for next turn."
    )


class TutorState(TypedDict):
    user_id: str
    session_id: str
    user_input: str
    assessment: AssessmentResult
    plan: LearningPlan
    retrieved_docs: list[KnowledgeItem]
    memory: SessionMemory | None
    tutor_output: TutorOutput | None


def _load_local_env() -> None:
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


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z]+", text.lower())


def _load_kb() -> list[KnowledgeItem]:
    if not KB_PATH.exists():
        return []
    payload = json.loads(KB_PATH.read_text(encoding="utf-8"))
    return [KnowledgeItem.model_validate(item) for item in payload]


def _load_all_memory() -> dict[str, dict]:
    if not MEMORY_PATH.exists():
        return {}
    return json.loads(MEMORY_PATH.read_text(encoding="utf-8"))


def _save_all_memory(all_memory: dict[str, dict]) -> None:
    MEMORY_PATH.write_text(
        json.dumps(all_memory, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )


class TutorAgent:
    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gemini-2.5-flash-lite",
    ) -> None:
        _load_local_env()
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Missing GEMINI_API_KEY. Add it to .env or pass api_key.")
        self.model = model
        self.client = genai.Client(api_key=self.api_key)
        self.knowledge_base = _load_kb()

    def _retrieve_docs(self, state: TutorState, top_k: int = 3) -> list[KnowledgeItem]:
        if not self.knowledge_base:
            return []
        query_tokens = set(
            _tokenize(
                " ".join(
                    [
                        state["user_input"],
                        state["assessment"].recommended_focus,
                        " ".join(state["assessment"].weak_areas),
                        " ".join(state["plan"].priority_skills),
                    ]
                )
            )
        )
        current_level = state["assessment"].level
        scored: list[tuple[int, KnowledgeItem]] = []
        for item in self.knowledge_base:
            if item.level != current_level:
                continue
            item_tokens = set(_tokenize(f"{item.topic} {item.content} {item.exercise}"))
            overlap = len(query_tokens & item_tokens)
            scored.append((overlap, item))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item for score, item in scored if score > 0][:top_k]

    def _get_or_create_memory(self, user_id: str, session_id: str) -> SessionMemory:
        all_memory = _load_all_memory()
        key = f"{user_id}:{session_id}"
        stored = all_memory.get(key)
        if stored:
            return SessionMemory.model_validate(stored)
        return SessionMemory(user_id=user_id, session_id=session_id)

    def _save_memory(self, memory: SessionMemory) -> None:
        all_memory = _load_all_memory()
        key = f"{memory.user_id}:{memory.session_id}"
        all_memory[key] = memory.model_dump()
        _save_all_memory(all_memory)

    def _build_prompt(self, state: TutorState) -> str:
        docs_text = "\n".join(
            [
                f"- [{doc.topic}] {doc.content} | Exercise: {doc.exercise}"
                for doc in state["retrieved_docs"]
            ]
        ) or "- No matching docs found in KB."

        memory = state["memory"]
        memory_text = (
            f"Recent topics: {', '.join(memory.recent_topics) if memory else ''}\n"
            f"Weak areas in memory: {', '.join(memory.known_weak_areas) if memory else ''}\n"
            f"Strong areas in memory: {', '.join(memory.known_strong_areas) if memory else ''}\n"
            f"Last difficulty: {memory.last_difficulty if memory else 'same'}\n"
            f"Progress notes: {', '.join(memory.progress_notes[-3:]) if memory else ''}"
        )

        return f"""
You are a friendly language tutor.
You receive the learner profile, a weekly plan, retrieved learning content (RAG), and session memory.
Generate one adaptive tutor reply for this turn in strict JSON.

Learner assessment (Bot 1):
- Level: {state["assessment"].level}
- Weak areas: {", ".join(state["assessment"].weak_areas)}
- Strong areas: {", ".join(state["assessment"].strong_areas)}
- Recommended focus: {state["assessment"].recommended_focus}

Learning plan (Bot 2):
- Target level: {state["plan"].target_level}
- Priority skills: {", ".join(state["plan"].priority_skills)}
- Plan summary: {state["plan"].summary}

Session memory:
{memory_text}

RAG context:
{docs_text}

User input:
{state["user_input"]}

Rules:
- Keep tutor_message concise (3-6 lines).
- Suggested exercise must be concrete and aligned with weak areas.
- difficulty_adjustment must be one of: easier, same, harder.
- memory_note should be one short sentence for next turn.
""".strip()

    def _generate_tutor_output(self, state: TutorState) -> TutorOutput:
        prompt = self._build_prompt(state)
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.4,
                response_mime_type="application/json",
                response_schema=TutorOutput,
            ),
        )

        parsed = getattr(response, "parsed", None)
        if isinstance(parsed, TutorOutput):
            return parsed
        if isinstance(parsed, dict):
            return TutorOutput.model_validate(parsed)

        text = getattr(response, "text", None)
        if not text:
            raise ValueError("Tutor model returned no parsed payload or text.")
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Tutor model returned invalid JSON: {text}") from exc
        try:
            return TutorOutput.model_validate(data)
        except ValidationError as exc:
            raise ValueError(f"Tutor output failed schema validation: {data}") from exc

    def _update_memory_from_output(self, state: TutorState) -> SessionMemory:
        memory = state["memory"] or SessionMemory(
            user_id=state["user_id"], session_id=state["session_id"]
        )
        output = state["tutor_output"]
        if output is None:
            return memory

        memory.recent_topics = (memory.recent_topics + [output.focus_topic])[-6:]
        memory.known_weak_areas = sorted(
            set(memory.known_weak_areas + state["assessment"].weak_areas)
        )[:10]
        memory.known_strong_areas = sorted(
            set(memory.known_strong_areas + state["assessment"].strong_areas)
        )[:10]
        memory.last_difficulty = output.difficulty_adjustment
        memory.progress_notes = (memory.progress_notes + [output.memory_note])[-10:]
        return memory

    def _node_rag(self, state: TutorState) -> TutorState:
        docs = self._retrieve_docs(state)
        return {**state, "retrieved_docs": docs}

    def _node_memory_load(self, state: TutorState) -> TutorState:
        memory = self._get_or_create_memory(state["user_id"], state["session_id"])
        return {**state, "memory": memory}

    def _node_generate(self, state: TutorState) -> TutorState:
        output = self._generate_tutor_output(state)
        return {**state, "tutor_output": output}

    def _node_memory_save(self, state: TutorState) -> TutorState:
        updated = self._update_memory_from_output(state)
        self._save_memory(updated)
        return {**state, "memory": updated}

    def build_graph(self):
        graph = StateGraph(TutorState)
        graph.add_node("rag", self._node_rag)
        graph.add_node("memory_load", self._node_memory_load)
        graph.add_node("generate", self._node_generate)
        graph.add_node("memory_save", self._node_memory_save)
        graph.set_entry_point("rag")
        graph.add_edge("rag", "memory_load")
        graph.add_edge("memory_load", "generate")
        graph.add_edge("generate", "memory_save")
        graph.add_edge("memory_save", END)
        return graph.compile()

    def respond(
        self,
        user_id: str,
        session_id: str,
        user_input: str,
        assessment: AssessmentResult,
        plan: LearningPlan,
    ) -> TutorOutput:
        app = self.build_graph()
        final_state = app.invoke(
            {
                "user_id": user_id,
                "session_id": session_id,
                "user_input": user_input,
                "assessment": assessment,
                "plan": plan,
                "retrieved_docs": [],
                "memory": None,
                "tutor_output": None,
            }
        )
        output = final_state["tutor_output"]
        if output is None:
            raise ValueError("Tutor graph finished without output.")
        return output


if __name__ == "__main__":
    # Demo with synthetic Bot 1 + Bot 2 outputs.
    assessment = AssessmentResult(
        level="A2",
        reasoning="Learner can produce simple connected sentences but makes tense mistakes.",
        vocabulary_score=3,
        grammar_score=2,
        fluency_score=3,
        weak_areas=["past tense consistency", "sentence connectors"],
        strong_areas=["basic self-introduction", "daily routine vocabulary"],
        recommended_focus="Practice past tense and linking words in short narratives.",
    )
    plan = LearningPlan(
        level="A2",
        target_level="B1",
        duration_weeks=4,
        weekly_goals=[
            {"week": 1, "focus": "Past tense basics", "exercises": ["Write 5 past-tense sentences", "Read and repeat short story"]},
            {"week": 2, "focus": "Connectors", "exercises": ["Use because/then/after in diary", "Combine short sentences"]},
            {"week": 3, "focus": "Speaking fluency", "exercises": ["1-minute daily recap", "Shadowing practice"]},
            {"week": 4, "focus": "Mixed review", "exercises": ["Describe yesterday in 8 lines", "Self-correction checklist"]},
        ],
        priority_skills=["grammar", "fluency"],
        summary="Build control of past tense and improve sentence flow.",
    )

    agent = TutorAgent()
    reply = agent.respond(
        user_id="demo-user",
        session_id="session-1",
        user_input="Can we practice speaking about what I did yesterday?",
        assessment=assessment,
        plan=plan,
    )
    print(reply.model_dump_json(indent=2))
