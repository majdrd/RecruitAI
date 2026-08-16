"""Conversation Info Advisor: LangChain tool agent + Chroma retrieval."""

import json
import os

from langchain.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from app.modules.config import DEFAULT_MODEL, PROMPTS_DIR
from app.modules.embedding.embed_pdf import retrieve_job_info as search_job_description

try:
    from langchain.agents import AgentExecutor, create_openai_tools_agent
except ImportError:
    from langchain.agents import AgentExecutor, create_tool_calling_agent as create_openai_tools_agent


@tool
def retrieve_job_info(query: str) -> str:
    """Search the Python Developer job description for facts that answer the candidate."""
    return search_job_description(query)


def _load_prompt():
    text = (PROMPTS_DIR / "info_advisor.txt").read_text(encoding="utf-8")
    return text.replace("{", "{{").replace("}", "}}")


def _build_executor(verbose=False):
    tools = [retrieve_job_info]
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


def advise(history_text, verbose=False):
    """Process chat history and return an info decision plus an optional answer."""
    user_input = f"Full conversation:\n{history_text}"
    executor = _build_executor(verbose=verbose)
    output = executor.invoke({"input": user_input})["output"]
    parsed = _parse_advisor_json(output)
    parsed.setdefault("decision", "info_not_needed")
    parsed["raw_output"] = output
    return parsed


if __name__ == "__main__":
    history = (
        "Assistant: Do you have any questions of your own?\n"
        "Candidate: Could you share more about the company's cloud technologies?"
    )
    print(advise(history, verbose=True))
