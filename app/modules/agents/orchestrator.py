"""Python control layer: one conversation turn with optional advisor loop."""

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
    exit_result = advisor_results.get("exit") or {}
    sched_result = advisor_results.get("sched") or {}
    if exit_result.get("decision") == "end":
        return "end"
    if sched_result.get("decision") == "sched":
        return "schedule"
    return "continue"


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
        return conversation_dt.replace(tzinfo=None) if conversation_dt.tzinfo else conversation_dt
    if isinstance(conversation_dt, str):
        return datetime.fromisoformat(conversation_dt.replace("Z", "+00:00")).replace(tzinfo=None)
    return datetime.now()


def handle_turn(user_input, session_id="default", conversation_dt=None):
    """Run one user turn and return action, message, and advisor results."""
    conversation_dt = _parse_conversation_dt(conversation_dt)
    history = get_history(session_id)
    history.add_user_message(user_input)

    advisor_notes = []
    advisor_results = {"exit": None, "sched": None, "info": None}
    message = ""

    for _ in range(MAX_ADVISOR_CALLS):
        # First decision in the diagram: pick one of the three advisors.
        # The Main Agent cannot reach the candidate without consulting one.
        advisor = main_agent.choose_advisor(history.messages, advisor_notes)
        result = consult_advisor(advisor, history, conversation_dt)
        advisor_results[advisor] = result
        advisor_notes.append(f"{ADVISOR_LABELS[advisor]}: {result}")

        # Second decision: consult another advisor, or send the message.
        decision = main_agent.decide_reply(history.messages, advisor_notes)
        if decision["next"] == "respond":
            message = decision["user_message"]
            break
    else:
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
    """Eval path: Exit + Sched vote, then apply end > schedule > continue."""
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
