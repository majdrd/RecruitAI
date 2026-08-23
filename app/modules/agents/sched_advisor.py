"""Interview Scheduling Advisor: LangChain tool agent + SQLAlchemy slots."""

import json
import os
from datetime import datetime

from langchain.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from app.modules.config import DEFAULT_MODEL, DEFAULT_POSITION, PROMPTS_DIR
from app.modules.database.db import format_slots, get_nearest_slots

try:
    from langchain.agents import AgentExecutor, create_openai_tools_agent
except ImportError:
    from langchain.agents import AgentExecutor, create_tool_calling_agent as create_openai_tools_agent


@tool
def get_available_slots(start_date: str, start_time: str = "09:00", position: str = DEFAULT_POSITION) -> str:
    """Return the 3 nearest available interview slots on or after a date and time.

    start_date must be YYYY-MM-DD. start_time must be HH:MM (24-hour).
    """
    try:
        after_dt = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M")
    except ValueError:
        after_dt = datetime.strptime(start_date, "%Y-%m-%d")
    slots = get_nearest_slots(after_dt, position=position, limit=3)
    if not slots:
        return "No available slots found after that date."
    return json.dumps(slots)


def _load_prompt():
    text = (PROMPTS_DIR / "sched_advisor.txt").read_text(encoding="utf-8")
    return text.replace("{", "{{").replace("}", "}}")


def _build_executor(verbose=False):
    tools = [get_available_slots]
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", _load_prompt()),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
            ("user", "{input}"),
        ]
    )
    llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL", DEFAULT_MODEL), temperature=0)
    agent = create_openai_tools_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=verbose)


def _parse_advisor_json(text):
    if not text:
        return {}
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.replace("json", "", 1).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1:
            try:
                return json.loads(cleaned[start : end + 1])
            except json.JSONDecodeError:
                return {"raw": cleaned}
        return {"raw": cleaned}


def advise(history_text, conversation_dt=None, verbose=False):
    """Process chat history and return a scheduling decision, with slots when needed."""
    if conversation_dt is None:
        conversation_dt = datetime.now()
    if isinstance(conversation_dt, str):
        conversation_dt = datetime.fromisoformat(conversation_dt.replace("Z", "+00:00")).replace(tzinfo=None)

    user_input = (
        f"Conversation current date/time: {conversation_dt.strftime('%Y-%m-%d %H:%M')}\n\n"
        f"Full conversation:\n{history_text}"
    )
    executor = _build_executor(verbose=verbose)
    output = executor.invoke({"input": user_input})["output"]
    parsed = _parse_advisor_json(output)
    parsed.setdefault("decision", "dont_sched")
    parsed["raw_output"] = output

    if parsed.get("decision") == "sched" and not parsed.get("slots"):
        slots = get_nearest_slots(conversation_dt, position=DEFAULT_POSITION, limit=3)
        parsed["slots"] = format_slots(slots)
    return parsed


if __name__ == "__main__":
    history = (
        "Assistant: Thanks for applying to our Python Developer opening.\n"
        "Candidate: Sounds great! I'd be happy to schedule a meeting"
    )
    print(advise(history, conversation_dt=datetime.now(), verbose=True))
