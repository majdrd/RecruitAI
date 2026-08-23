"""Main Agent: the two decisions the workflow diagram gives it.

First it picks one of the three advisors, then, once that advisor has answered,
it decides whether to consult another one or to write the candidate's message.
"""

import os

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from app.modules.config import DEFAULT_MODEL, PROMPTS_DIR

ADVISORS = ("exit", "sched", "info")


def _load_prompt(filename):
    # Prompt files contain JSON examples. Escape braces so LangChain
    # does not treat {"next"} / {"advisor"} as template variables.
    text = (PROMPTS_DIR / filename).read_text(encoding="utf-8")
    return text.replace("{", "{{").replace("}", "}}")


def _build_chain(filename, user_template):
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", _load_prompt(filename)),
            MessagesPlaceholder(variable_name="history"),
            ("user", user_template),
        ]
    )
    llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL", DEFAULT_MODEL), temperature=0)
    return prompt | llm | JsonOutputParser()


def format_history_messages(messages):
    lines = []
    for message in messages:
        role = getattr(message, "type", "message").capitalize()
        lines.append(f"{role}: {message.content}")
    return "\n".join(lines)


def _format_notes(advisor_notes):
    return "\n".join(advisor_notes) if advisor_notes else "None yet."


def choose_advisor(history_messages, advisor_notes):
    """First decision: one of exit, sched or info. Never talks to the candidate."""
    chain = _build_chain(
        "main_agent_advisor.txt",
        "Advisor notes so far:\n{advisor_notes}\n\n"
        "Return JSON with keys advisor and reason.",
    )
    result = chain.invoke(
        {
            "history": history_messages,
            "advisor_notes": _format_notes(advisor_notes),
        }
    )
    advisor = ""
    if isinstance(result, dict):
        advisor = str(result.get("advisor", "")).strip().lower()
    # Falling back to the Exit Advisor keeps a missed opt-out from being
    # answered as if the candidate were still interested.
    return advisor if advisor in ADVISORS else "exit"


def decide_reply(history_messages, advisor_notes, force_respond=False):
    """Second decision: consult another advisor, or send the message."""
    chain = _build_chain(
        "main_agent_reply.txt",
        "Advisor notes:\n{advisor_notes}\n\n"
        "Force respond: {force_respond}\n"
        "Return JSON with keys next and user_message.",
    )
    result = chain.invoke(
        {
            "history": history_messages,
            "advisor_notes": _format_notes(advisor_notes),
            "force_respond": "yes" if force_respond else "no",
        }
    )
    if not isinstance(result, dict):
        result = {"next": "respond", "user_message": str(result)}

    nxt = str(result.get("next", "")).strip().lower()
    if nxt not in {"consult_again", "respond"}:
        nxt = "respond"
    if force_respond:
        nxt = "respond"

    return {"next": nxt, "user_message": result.get("user_message") or ""}
