"""Python control layer: one conversation turn with optional advisor loop."""
# Help: Lesson 22 - GenAI (DL) - LangChain (Agents & Tools, Example 5: Multi-Agent + memory)

import re
from datetime import datetime

from langchain_community.chat_message_histories import ChatMessageHistory

from app.modules.agents import exit_advisor, info_advisor, main_agent, sched_advisor

MAX_ADVISOR_CALLS = 3
SESSION_STORE = {}
ADVISOR_LABELS = {
    "exit": "Exit Advisor",
    "sched": "Sched Advisor",
    "info": "Info Advisor",
}


def get_history(session_id):
    if session_id not in SESSION_STORE:
        SESSION_STORE[session_id] = ChatMessageHistory()
    return SESSION_STORE[session_id]


def reset_session(session_id):
    SESSION_STORE[session_id] = ChatMessageHistory()
    return SESSION_STORE[session_id]


def format_history(history):
    return main_agent.format_history_messages(history.messages)


def resolve_action(advisor_results):
    """Priority when advisors disagree: end > schedule > continue."""
    exit_result = advisor_results.get("exit") or {}
    sched_result = advisor_results.get("sched") or {}

    if exit_result.get("decision") == "end":
        return "end"
    if sched_result.get("decision") == "sched":
        return "schedule"
    return "continue"


def candidate_locked_a_slot(history):
    """True when the latest user message accepts a specific offered interview time.

    Prompts alone were not enough: after "14:00 is fine" the Main Agent often
    called Sched again and never closed the chat. This small rule forces Exit.
    """
    messages = history.messages
    if len(messages) < 2:
        return False

    last = messages[-1]
    if getattr(last, "type", "") != "human":
        return False
    user_text = (last.content or "").strip().lower()
    if not user_text:
        return False

    prev_ai = ""
    for message in reversed(messages[:-1]):
        if getattr(message, "type", "") == "ai":
            prev_ai = (message.content or "").lower()
            break
    if not prev_ai:
        return False

    # Previous recruiter message should look like it offered times.
    offers_times = False
    for token in (":00", " am", " pm", "slot", "available", "which time", "which one", "september"):
        if token in prev_ai:
            offers_times = True
            break
    if not offers_times:
        return False

    acceptance_phrases = (
        "is fine",
        "works for me",
        "works",
        "i'll take",
        "ill take",
        "book that",
        "that one",
        "sounds good",
        "perfect",
        "confirm",
        "go with",
        "i take",
    )
    for phrase in acceptance_phrases:
        if phrase in user_text:
            return True

    if re.search(r"\b([01]?\d|2[0-3]):[0-5]\d\b", user_text):
        return True
    if re.search(r"\b([1-9]|1[0-2])\s?(am|pm)\b", user_text):
        return True
    return False


def consult_advisor(advisor, history, conversation_dt):
    """Send the full chat history to one advisor and return its decision."""
    history_text = format_history(history)
    if advisor == "sched":
        return sched_advisor.advise(history_text, conversation_dt)
    if advisor == "info":
        return info_advisor.advise(history_text)
    return exit_advisor.predict(history_text)


def _parse_conversation_dt(conversation_dt):
    if conversation_dt is None:
        return datetime.now()
    if isinstance(conversation_dt, datetime):
        return conversation_dt
    if isinstance(conversation_dt, str):
        # Accept ISO strings from the Streamlit sidebar / eval path.
        text = conversation_dt.replace("Z", "")
        return datetime.fromisoformat(text)
    return datetime.now()


def handle_turn(user_input, session_id="default", conversation_dt=None):
    """Run one user turn and return action, message, and advisor results."""
    conversation_dt = _parse_conversation_dt(conversation_dt)
    history = get_history(session_id)
    history.add_user_message(user_input)

    advisor_notes = []
    advisor_results = {"exit": None, "sched": None, "info": None}
    message = ""
    booking_close = candidate_locked_a_slot(history)

    for _ in range(MAX_ADVISOR_CALLS):
        # First decision: pick one advisor. The candidate never hears from this step.
        # Exception: if the candidate just locked a slot, go straight to Exit.
        if booking_close and advisor_results["exit"] is None:
            advisor = "exit"
        else:
            advisor = main_agent.choose_advisor(history.messages, advisor_notes)

        result = consult_advisor(advisor, history, conversation_dt)

        # Safety net: a locked slot must close the chat even if Exit is unsure.
        if booking_close and advisor == "exit" and result.get("decision") != "end":
            result = {
                "decision": "end",
                "reason": "The candidate confirmed an interview slot.",
                "source": "rule",
            }

        advisor_results[advisor] = result
        advisor_notes.append(f"{ADVISOR_LABELS[advisor]}: {result}")

        # Second decision: consult again, or send the reply.
        decision = main_agent.decide_reply(history.messages, advisor_notes)
        if decision["next"] == "respond":
            message = decision["user_message"]
            break
    else:
        # Cap reached — force a candidate-facing reply.
        decision = main_agent.decide_reply(history.messages, advisor_notes, force_respond=True)
        message = decision["user_message"]

    if not message:
        decision = main_agent.decide_reply(history.messages, advisor_notes, force_respond=True)
        message = decision["user_message"] or "Thanks for your message."

    action = resolve_action(advisor_results)
    history.add_ai_message(message)
    return {
        "action": action,
        "message": message,
        "advisors": advisor_results,
    }


def predict_action(history_text, conversation_dt=None):
    """Eval path: Exit first; if not end, Sched; skip Info (maps to continue anyway)."""
    conversation_dt = _parse_conversation_dt(conversation_dt)

    exit_result = exit_advisor.predict(history_text)
    if exit_result.get("decision") == "end":
        return {
            "action": "end",
            "advisors": {"exit": exit_result, "sched": None, "info": None},
        }

    sched_result = sched_advisor.advise(history_text, conversation_dt)
    advisors = {"exit": exit_result, "sched": sched_result, "info": None}
    return {
        "action": resolve_action(advisors),
        "advisors": advisors,
    }
