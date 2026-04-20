"""
Streamlit web app for the Adaptive AI Language Tutor.

Flow:
  1. Welcome screen  — user picks language and starts
  2. Assessment      — 4 questions collected via chat UI
  3. Processing      — assessment + planning pipeline runs
  4. Lesson          — interactive tutor chat (warm_up → exercises → summary)
"""

import os
import sys

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(__file__))

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="AI Language Tutor",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS overrides ─────────────────────────────────────────────────────────────

st.markdown(
    """
<style>
.exercise-box {
    background: #f0f4ff;
    border-left: 4px solid #4a6cf7;
    padding: 12px 16px;
    border-radius: 6px;
    margin: 8px 0;
    font-size: 0.97em;
}
.feedback-correct {
    background: #f0fff4;
    border-left: 4px solid #38a169;
    padding: 12px 16px;
    border-radius: 6px;
    margin: 8px 0;
}
.feedback-wrong {
    background: #fff5f5;
    border-left: 4px solid #e53e3e;
    padding: 12px 16px;
    border-radius: 6px;
    margin: 8px 0;
}
.level-badge {
    display: inline-block;
    background: #4a6cf7;
    color: white;
    padding: 4px 14px;
    border-radius: 20px;
    font-weight: bold;
    font-size: 1.1em;
}
.score-row {
    display: flex;
    gap: 12px;
    margin: 8px 0;
}
.score-chip {
    background: #eef2ff;
    border-radius: 8px;
    padding: 4px 10px;
    font-size: 0.85em;
}
</style>
""",
    unsafe_allow_html=True,
)

# ── Session state init ────────────────────────────────────────────────────────

DEFAULTS = {
    "phase": "welcome",           # welcome | assessment | processing | lesson
    "assessment_step": 0,         # 0-3 (which question we're on)
    "language_samples": [],       # collected answers
    "target_language": "English",
    "assessment_result": None,
    "learning_plan": None,
    "memory": None,
    "conversation": [],           # Anthropic message history
    "exercise_history": [],
    "chat_display": [],           # list of {"role", "content", "type"} for display
    "error": None,
}

for key, val in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ── Lazy imports (avoid import errors on page load) ───────────────────────────

@st.cache_resource(show_spinner=False)
def _load_agents():
    from src.graph.pipeline import run_setup
    from src.agents.tutor_agent import SessionMemory, run_tutor_turn
    from src.agents.assessment_agent import AssessmentResult
    from src.agents.planning_agent import LearningPlan
    return run_setup, SessionMemory, run_tutor_turn, AssessmentResult, LearningPlan

# ── Constants ─────────────────────────────────────────────────────────────────

ASSESSMENT_PROMPTS = [
    "Tell me about yourself — your name, where you're from, and why you want to learn this language.",
    "Describe what you did yesterday from morning to evening.",
    "What do you think is the hardest part of learning a new language? Explain your opinion.",
    "Describe a place that is important to you and explain why it matters to you.",
]

LEVEL_LABELS = {"A1": "Beginner", "A2": "Elementary", "B1": "Intermediate", "B2": "Upper-Intermediate"}
LEVEL_COLORS = {"A1": "#68d391", "A2": "#63b3ed", "B1": "#f6ad55", "B2": "#fc8181"}

LANGUAGES = ["English", "Spanish", "French", "German", "Italian", "Portuguese"]

# ── Helper ─────────────────────────────────────────────────────────────────────

def _check_api_keys() -> tuple[bool, list[str]]:
    missing = []
    if not os.environ.get("GEMINI_API_KEY"):
        missing.append("GEMINI_API_KEY")
    if not os.environ.get("OPENAI_API_KEY"):
        missing.append("OPENAI_API_KEY")
    return len(missing) == 0, missing

def _stars(score: int) -> str:
    return "★" * score + "☆" * (5 - score)

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("🌍 Language Tutor")

    if st.session_state.assessment_result:
        r = st.session_state.assessment_result
        level = r["level"]
        st.markdown(
            f"<div class='level-badge' style='background:{LEVEL_COLORS[level]}'>"
            f"{level} — {LEVEL_LABELS[level]}</div>",
            unsafe_allow_html=True,
        )
        st.caption(r["reasoning"])

        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        col1.metric("Vocab", _stars(r["vocabulary_score"]))
        col2.metric("Grammar", _stars(r["grammar_score"]))
        col3.metric("Fluency", _stars(r["fluency_score"]))

        st.markdown("**Weak areas**")
        for area in r["weak_areas"]:
            st.markdown(f"- {area}")

        st.markdown("**Strong areas**")
        for area in r["strong_areas"]:
            st.markdown(f"- {area}")

    if st.session_state.learning_plan:
        plan = st.session_state.learning_plan
        st.markdown("---")
        st.markdown("**12-Week Plan**")
        st.caption(plan["summary"])
        st.markdown("**Priority skills**")
        for skill in plan["priority_skills"]:
            st.markdown(f"- {skill}")

    if st.session_state.memory:
        mem = st.session_state.memory
        st.markdown("---")
        st.markdown("**Session progress**")
        exercise_count = mem.get("exercise_count", 0)
        st.progress(exercise_count / 5, text=f"Exercises: {exercise_count}/5")
        diff = mem.get("current_difficulty", "same")
        diff_icons = {"easier": "🔽 Easier", "same": "➡️ Same", "harder": "🔼 Harder"}
        st.caption(f"Difficulty: {diff_icons.get(diff, diff)}")

    st.markdown("---")
    if st.button("🔄 Start over", use_container_width=True):
        for key in DEFAULTS:
            st.session_state[key] = DEFAULTS[key]
        st.rerun()

# ── Phase: Welcome ────────────────────────────────────────────────────────────

if st.session_state.phase == "welcome":
    st.markdown("# 🌍 AI Language Tutor")
    st.markdown(
        "An adaptive tutor that **assesses your current level**, builds a **personalized "
        "12-week plan**, and teaches you through **interactive exercises with real feedback**."
    )

    st.markdown("---")

    keys_ok, missing = _check_api_keys()
    if not keys_ok:
        st.error(
            f"**Missing API keys: {', '.join(missing)}**\n\n"
            "Create a `.env` file at the project root with:\n\n"
            "```\nGEMINI_API_KEY=your_gemini_key\nOPENAI_API_KEY=your_openai_key\n```"
        )
    else:
        col1, col2 = st.columns(2)
        with col1:
            lang = st.selectbox("I want to learn:", LANGUAGES, index=0)
            st.session_state.target_language = lang
        with col2:
            st.markdown(" ")
            st.markdown(" ")
            if st.button("Start Assessment →", type="primary", use_container_width=True):
                st.session_state.phase = "assessment"
                st.rerun()

        st.markdown("---")
        st.markdown("### How it works")
        cols = st.columns(3)
        cols[0].markdown("**① Assessment**\n\nAnswer 4 questions so the AI can understand your current level.")
        cols[1].markdown("**② Personal Plan**\n\nGet a 12-week learning plan built specifically for your gaps.")
        cols[2].markdown("**③ Adaptive Lessons**\n\nPractice exercises that get harder as you improve, with detailed feedback.")

# ── Phase: Assessment ─────────────────────────────────────────────────────────

elif st.session_state.phase == "assessment":
    step = st.session_state.assessment_step
    total = len(ASSESSMENT_PROMPTS)

    st.markdown("## 📝 Assessment")
    st.progress((step) / total, text=f"Question {step + 1} of {total}")
    st.markdown("---")

    # Show previous Q&A
    for i, (q, a) in enumerate(
        zip(ASSESSMENT_PROMPTS, st.session_state.language_samples)
    ):
        with st.chat_message("assistant"):
            st.markdown(q)
        with st.chat_message("user"):
            st.markdown(a)

    # Current question
    if step < total:
        with st.chat_message("assistant"):
            st.markdown(ASSESSMENT_PROMPTS[step])

        answer = st.chat_input("Your answer…")
        if answer:
            st.session_state.language_samples.append(answer)
            st.session_state.assessment_step += 1

            if st.session_state.assessment_step >= total:
                st.session_state.phase = "processing"

            st.rerun()

# ── Phase: Processing ─────────────────────────────────────────────────────────

elif st.session_state.phase == "processing":
    st.markdown("## ⚙️ Analyzing your level…")
    st.markdown("This takes about 20–30 seconds.")

    progress_bar = st.progress(0, text="Running assessment agent…")

    try:
        run_setup, SessionMemory, run_tutor_turn, AssessmentResult, LearningPlan = _load_agents()

        progress_bar.progress(30, text="Assessment complete — building your plan…")
        state = run_setup(
            st.session_state.language_samples,
            st.session_state.target_language,
        )

        progress_bar.progress(80, text="Plan ready — starting your first lesson…")
        st.session_state.assessment_result = state["assessment_result"]
        st.session_state.learning_plan = state["learning_plan"]

        # Init memory and first tutor greeting
        mem = SessionMemory()
        st.session_state.memory = mem.model_dump()

        assessment = AssessmentResult(**state["assessment_result"])
        plan = LearningPlan(**state["learning_plan"])

        greeting_resp, new_mem, new_conv, new_hist = run_tutor_turn(
            user_message="Hello! I'm ready to start.",
            assessment=assessment,
            plan=plan,
            memory=mem,
            conversation=[],
            exercise_history=[],
        )

        st.session_state.memory = new_mem.model_dump()
        st.session_state.conversation = new_conv
        st.session_state.exercise_history = new_hist

        # Store first message for display
        st.session_state.chat_display = [
            {"role": "assistant", "content": greeting_resp.message, "type": "message"}
        ]
        if greeting_resp.exercise:
            st.session_state.chat_display.append(
                {
                    "role": "assistant",
                    "content": greeting_resp.exercise.model_dump(),
                    "type": "exercise",
                }
            )

        progress_bar.progress(100, text="Done!")
        st.session_state.phase = "lesson"
        st.rerun()

    except Exception as e:
        st.session_state.error = str(e)
        st.session_state.phase = "welcome"
        st.error(f"Something went wrong: {e}")
        st.stop()

# ── Phase: Lesson ─────────────────────────────────────────────────────────────

elif st.session_state.phase == "lesson":
    level = (st.session_state.assessment_result or {}).get("level", "")
    level_color = LEVEL_COLORS.get(level, "#4a6cf7")
    st.markdown(
        f"## 💬 Your Lesson  "
        f"<span class='level-badge' style='background:{level_color}'>"
        f"{level}</span>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    # ── Display chat history ──
    for msg in st.session_state.chat_display:
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.markdown(msg["content"])
        else:
            if msg["type"] == "message":
                with st.chat_message("assistant"):
                    st.markdown(msg["content"])
            elif msg["type"] == "exercise":
                ex = msg["content"]
                with st.chat_message("assistant"):
                    ex_type_label = ex["type"].replace("_", " ").title()
                    st.markdown(
                        f"<div class='exercise-box'>"
                        f"<strong>📝 {ex_type_label}</strong> "
                        f"<em>(topic: {ex.get('topic', '')})</em><br><br>"
                        f"{ex['prompt']}"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
            elif msg["type"] == "feedback_correct":
                fb = msg["content"]
                with st.chat_message("assistant"):
                    st.markdown(
                        f"<div class='feedback-correct'>"
                        f"<strong>✓ Correct!</strong><br>"
                        f"{fb['explanation']}<br><br>"
                        f"<em>Follow-up: {fb['follow_up_exercise']}</em>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
            elif msg["type"] == "feedback_wrong":
                fb = msg["content"]
                with st.chat_message("assistant"):
                    correction = (
                        f"<br><strong>Correction:</strong> {fb['corrected_version']}"
                        if fb.get("corrected_version")
                        else ""
                    )
                    st.markdown(
                        f"<div class='feedback-wrong'>"
                        f"<strong>✗ Not quite.</strong><br>"
                        f"{fb['explanation']}"
                        f"{correction}<br><br>"
                        f"<em>Follow-up: {fb['follow_up_exercise']}</em>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
            elif msg["type"] == "summary":
                with st.chat_message("assistant"):
                    st.success(msg["content"])

    # ── Check if session is complete ──
    mem = st.session_state.memory or {}
    if mem.get("phase") == "summary" and st.session_state.chat_display:
        last = st.session_state.chat_display[-1]
        if last.get("type") == "summary":
            st.balloons()
            st.success("🎉 Session complete! Check the sidebar for your progress.")
            if st.button("Start new session", type="primary"):
                # Keep assessment + plan, reset memory + conversation
                run_setup, SessionMemory, run_tutor_turn, AssessmentResult, LearningPlan = _load_agents()
                new_mem = SessionMemory()
                st.session_state.memory = new_mem.model_dump()
                st.session_state.conversation = []
                st.session_state.exercise_history = []
                st.session_state.chat_display = []
                st.rerun()
            st.stop()

    # ── Chat input ──
    user_input = st.chat_input("Type your answer or message…")
    if user_input:
        run_setup, SessionMemory_cls, run_tutor_turn, AssessmentResult, LearningPlan = _load_agents()

        assessment = AssessmentResult(**st.session_state.assessment_result)
        plan = LearningPlan(**st.session_state.learning_plan)
        memory = SessionMemory_cls(**st.session_state.memory)

        with st.spinner("Tutor is responding…"):
            try:
                resp, new_mem, new_conv, new_hist = run_tutor_turn(
                    user_message=user_input,
                    assessment=assessment,
                    plan=plan,
                    memory=memory,
                    conversation=st.session_state.conversation,
                    exercise_history=st.session_state.exercise_history,
                )
            except Exception as e:
                st.error(f"Error: {e}")
                st.stop()

        st.session_state.memory = new_mem.model_dump()
        st.session_state.conversation = new_conv
        st.session_state.exercise_history = new_hist

        # Add user message to display
        st.session_state.chat_display.append(
            {"role": "user", "content": user_input, "type": "message"}
        )

        # Add tutor message
        if resp.message:
            msg_type = "summary" if resp.session_complete else "message"
            st.session_state.chat_display.append(
                {"role": "assistant", "content": resp.message, "type": msg_type}
            )

        # Add feedback
        if resp.feedback:
            fb_dict = resp.feedback.model_dump()
            fb_type = "feedback_correct" if resp.feedback.is_correct else "feedback_wrong"
            st.session_state.chat_display.append(
                {"role": "assistant", "content": fb_dict, "type": fb_type}
            )

        # Add exercise
        if resp.exercise and not resp.session_complete:
            st.session_state.chat_display.append(
                {
                    "role": "assistant",
                    "content": resp.exercise.model_dump(),
                    "type": "exercise",
                }
            )

        st.rerun()
