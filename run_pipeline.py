"""
End-to-end pipeline runner for:
Bot 1 (assessment) -> Bot 2 (planner) -> Bot 3 (tutor)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
ASSESSMENT_DIR = PROJECT_ROOT / "Assesment-agent"
PLANNER_DIR = PROJECT_ROOT / "planner-agent"
TUTOR_DIR = PROJECT_ROOT / "tutor-agent"

for candidate in (PROJECT_ROOT, ASSESSMENT_DIR, PLANNER_DIR, TUTOR_DIR):
    value = str(candidate)
    if candidate.exists() and value not in sys.path:
        sys.path.append(value)

from assessment_agent import AssessmentAgent  # noqa: E402
from planner_agent import PlanningAgent  # noqa: E402
from tutor_agent import TutorAgent  # noqa: E402


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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Bot1->Bot2->Bot3 pipeline."
    )
    parser.add_argument("--user-id", default="demo-user")
    parser.add_argument("--session-id", default="session-1")
    parser.add_argument("--answer1", required=True, help="Bot 1 question 1 answer")
    parser.add_argument("--answer2", required=True, help="Bot 1 question 2 answer")
    parser.add_argument("--answer3", required=True, help="Bot 1 question 3 answer")
    parser.add_argument("--answer4", required=True, help="Bot 1 question 4 answer")
    parser.add_argument(
        "--user-input",
        required=True,
        help="Current learner message for Bot 3 tutor turn",
    )
    parser.add_argument(
        "--json-only",
        action="store_true",
        help="Print only combined final JSON",
    )
    return parser.parse_args()


def main() -> None:
    load_local_env()
    args = parse_args()

    # Bot 1: Assessment
    agent1 = AssessmentAgent()
    assessment = agent1.assess(
        answer1=args.answer1,
        answer2=args.answer2,
        answer3=args.answer3,
        answer4=args.answer4,
    )

    # Bot 2: Planner
    agent2 = PlanningAgent()
    plan = agent2.create_plan(assessment=assessment)

    # Bot 3: Tutor
    agent3 = TutorAgent()
    tutor_output = agent3.respond(
        user_id=args.user_id,
        session_id=args.session_id,
        user_input=args.user_input,
        assessment=assessment,
        plan=plan,
    )

    combined = {
        "assessment": assessment.model_dump(),
        "plan": plan.model_dump(),
        "tutor_output": tutor_output.model_dump(),
    }

    if args.json_only:
        print(json.dumps(combined, indent=2, ensure_ascii=True))
        return

    print("=== BOT 1: ASSESSMENT ===")
    print(assessment.model_dump_json(indent=2))
    print("\n=== BOT 2: LEARNING PLAN ===")
    print(plan.model_dump_json(indent=2))
    print("\n=== BOT 3: TUTOR OUTPUT ===")
    print(tutor_output.model_dump_json(indent=2))
    print("\n=== COMBINED ===")
    print(json.dumps(combined, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
