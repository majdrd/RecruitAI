"""CLI entry point for local debugging of one conversation."""

import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.modules.agents.orchestrator import handle_turn, reset_session

OPENING = (
    "Hi, thanks for submitting your application for our Python Developer role. "
    "Could you share a bit about your Python experience?"
)


def main():
    session_id = "cli-user"
    history = reset_session(session_id)
    history.add_ai_message(OPENING)
    print("RecruitAI CLI. Type 'exit' to quit.")
    print(f"Recruiter: {OPENING}")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in {"exit", "quit"}:
            break
        if not user_input:
            continue
        result = handle_turn(
            user_input,
            session_id=session_id,
            conversation_dt=datetime.now(),
        )
        print(f"[{result['action']}] Recruiter: {result['message']}")
        if result["action"] == "end":
            break


if __name__ == "__main__":
    main()
