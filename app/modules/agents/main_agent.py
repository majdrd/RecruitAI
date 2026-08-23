# TODO: Main Agent — orchestrator brain, not a database client.
# The diagram gives it two separate decisions, so write two functions:
#   1. pick one advisor: exit | sched | info. This step never writes to the candidate.
#   2. once that advisor answers: consult_again | respond, plus the user_message.
# Both read the history + advisor notes, and each one needs its own prompt file.
# Write the candidate-facing SMS-style reply only when the second decision is respond.
# Never invent interview times; only use slots from Sched Advisor notes.
# Help: Lesson 22 - GenAI (DL) - LangChain (Models & Parsers, Chains)
# Help: Lesson 20 - GenAI (DL) - Prompt Engineering
