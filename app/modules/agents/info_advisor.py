"""Conversation Info Advisor: a LangChain tool agent over the job-description PDF."""
# Help: Lesson 22 - GenAI (DL) - LangChain (Agents & Tools)
# Help: Lesson 23 - GenAI - NLP & Embedding & Retrieval

import json
import os

from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from app.modules.config import DEFAULT_MODEL, PROMPTS_DIR
from app.modules.embedding.embed_pdf import retrieve_job_info as search_job_description


# The type hints are what LangChain uses to describe the tool to the model.
@tool
def retrieve_job_info(query: str) -> str:
    """Search the Python Developer job description for facts that answer the candidate."""
    return search_job_description(query)


def _load_prompt():
    # Escape the braces of the JSON examples, or ChatPromptTemplate reads them as variables.
    text = (PROMPTS_DIR / "info_advisor.txt").read_text(encoding="utf-8")
    return text.replace("{", "{{").replace("}", "}}")


def _build_executor(verbose=False):
    tools = [retrieve_job_info]
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


def advise(history_text, verbose=False):
    """Read the full chat history and decide info_needed or info_not_needed."""
    user_input = f"Full conversation:\n{history_text}"

    executor = _build_executor(verbose=verbose)
    output = executor.invoke({"input": user_input})["output"]

    result = _parse_json(output)
    result.setdefault("decision", "info_not_needed")

    # If the model said info_needed but left answer empty, search once more so the
    # Main Agent still has facts to work with.
    if result["decision"] == "info_needed" and not result.get("answer"):
        result["answer"] = search_job_description(history_text)

    return result


if __name__ == "__main__":
    history = (
        "Assistant: Do you have any questions of your own?\n"
        "Candidate: Could you share more about the company's cloud technologies?"
    )
    print(advise(history, verbose=True))
