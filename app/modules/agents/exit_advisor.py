"""Conversation Exit Advisor: prompt-engineered LLM decision."""
# Help: Lesson 20 - GenAI (DL) - Prompt Engineering
# Help: Lesson 22 - GenAI (DL) - LangChain (Models & Parsers)

import os

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.modules.config import DEFAULT_MODEL, PROMPTS_DIR

VALID_DECISIONS = {"end", "dont_end"}


def _load_prompt():
    # Escape the braces of the JSON examples, or ChatPromptTemplate reads them as variables.
    text = (PROMPTS_DIR / "exit_advisor.txt").read_text(encoding="utf-8")
    return text.replace("{", "{{").replace("}", "}}")


def _build_chain():
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", _load_prompt()),
            (
                "user",
                "Full conversation:\n{history}\n\n",
                "Return JSON with keys decision and reason.",
            ),
        ]
    )
    llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL", DEFAULT_MODEL), temperature=0)
    return prompt | llm | JsonOutputParser()


def predict(history_text):
    """Return {decision: end|dont_end, reason, source}."""
    chain = _build_chain()
    result = chain.invoke({"history": history_text or ""})
    if not isinstance(result, dict):
        result = {}

    decision = str(result.get("decision", "")).strip().lower()
    if decision not in VALID_DECISIONS:
        decision = "dont_end"

    return {
        "decision": decision,
        "reason": result.get("reason") or "no reason given",
        "source": "prompt",
    }


if __name__ == "__main__":
    samples = [
        "Candidate: Please remove me from your list. Thanks.",
        "Candidate: I have three years' experience with Django and Flask.",
    ]
    for sample in samples:
        print(sample)
        print(predict(sample))
        print()
