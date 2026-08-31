"""Interview Scheduling Advisor: a LangChain tool agent over the Schedule table."""
# Help: Lesson 22 - GenAI (DL) - LangChain (Agents & Tools)
# Help: Lesson 19 - GenAI - Venv & Function Calling

import json
import os
from datetime import datetime

from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from app.modules.config import DEFAULT_MODEL, DEFAULT_POSITION, PROMPTS_DIR
from app.modules.database.db import format_slots, get_nearest_slots


# The type hints are what LangChain uses to describe the tool to the model.
@tool
def get_available_slots(start_date: str, start_time: str = "09:00") -> str:
    """Return the 3 nearest available interview slots on or after a date and time.

    start_date must be YYYY-MM-DD. start_time must be HH:MM in 24-hour form.
    """
    try:
        after_dt = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M")
    except ValueError:
        return "Could not read that date. Use YYYY-MM-DD for the date and HH:MM for the time."

    slots = get_nearest_slots(after_dt, position=DEFAULT_POSITION, limit=3)
    if not slots:
        return "No available slots found after that date."
    return json.dumps(slots)


def _load_prompt():
    # Escape the braces of the JSON examples, or ChatPromptTemplate reads them as variables.
    text = (PROMPTS_DIR / "sched_advisor.txt").read_text(encoding="utf-8")
    return text.replace("{", "{{").replace("}", "}}")


def _build_executor(verbose=False):
    tools = [get_available_slots]
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", _load_prompt()),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )
    llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL", DEFAULT_MODEL), temperature=0)
    agent = create_openai_tools_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=verbose)


def _parse_json(text):
    """The agent answers with JSON as plain text, sometimes inside a code fence."""
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        return {}
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return {}


def advise(history_text, conversation_dt=None, verbose=False):
    """Read the full chat history and decide sched or dont_sched."""
    if conversation_dt is None:
        conversation_dt = datetime.now()

    user_input = (
        f"Conversation current date/time: {conversation_dt.strftime('%Y-%m-%d %H:%M')}\n\n"
        f"Full conversation:\n{history_text}"
    )

    executor = _build_executor(verbose=verbose)
    output = executor.invoke({"input": user_input})["output"]

    result = _parse_json(output)
    result.setdefault("decision", "dont_sched")

    # If the model decided sched but did not pass the slots through, look them up here
    # so the Main Agent never has to invent a time.
    if result["decision"] == "sched" and not result.get("slots"):
        result["slots"] = format_slots(get_nearest_slots(conversation_dt))

    return result


if __name__ == "__main__":
    history = (
        "Assistant: Thanks for applying to our Python Developer opening.\n"
        "Candidate: Sounds great! I'd be happy to schedule a meeting."
    )
    print(advise(history, verbose=True))
