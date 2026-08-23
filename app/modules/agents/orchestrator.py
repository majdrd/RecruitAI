# TODO: Python control layer for one conversation turn (Lesson 22 Example 5).
# Keep ChatMessageHistory per session_id. Loop: the Main Agent picks one advisor, that advisor
# reads the full history and answers, then the Main Agent consults again or sends the reply.
# At least one advisor runs before the candidate hears anything; cap at 3 advisor calls per turn.
# Priority if advisors disagree: end > schedule > continue.
# Help: Lesson 22 - GenAI (DL) - LangChain (Agents & Tools, Example 5: Multi-Agent + memory)
