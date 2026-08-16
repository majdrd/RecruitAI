"""Main Agent: routes to one advisor or writes the candidate-facing reply."""

import json
import os

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from app.modules.config import DEFAULT_MODEL, PROMPTS_DIR


def _load_prompt():
    # Prompt files contain JSON examples. Escape braces so LangChain
    # does not treat {"next"} / {"decision"} as template variables.
    text = (PROMPTS_DIR / "main_agent.txt").read_text(encoding="utf-8")
    return text.replace("{", "{{").replace("}", "}}")


def _build_chain():
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", _load_prompt()),
            MessagesPlaceholder(variable_name="history"),
            (
                "user",
                "Advisor notes:\n{advisor_notes}\n\n"
                "Force respond: {force_respond}\n"
                "Return JSON with keys next and user_message.",
            ),
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


def decide(history_messages, advisor_notes, force_respond=False):
    """Return {next: exit|sched|info|respond, user_message: str}."""
    notes_text = "\n".join(advisor_notes) if advisor_notes else "None yet."
    chain = _build_chain()
    result = chain.invoke(
        {
            "history": history_messages,
            "advisor_notes": notes_text,
            "force_respond": "yes" if force_respond else "no",
        }
    )
    if not isinstance(result, dict):
        result = {"next": "respond", "user_message": str(result)}
    result.setdefault("next", "respond")
    result.setdefault("user_message", "")
    if force_respond:
        result["next"] = "respond"
    return result
