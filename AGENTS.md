# RecruitAI — agent context

Student GenAI final project: a Streamlit recruiting chatbot (proof of concept) that talks to a
Python Developer candidate. It answers job questions from a PDF via Chroma RAG, offers interview
slots from a local SQLite `Schedule` table, and ends the chat when the candidate opts out.

## Architecture

A Main Agent orchestrates three advisors. It never queries SQL or Chroma itself.

- **Main Agent** — holds the session memory, picks one advisor per inner step, then either consults
  another advisor in the same turn or sends the user-facing reply. Cap the inner loop at 3 advisor
  calls. Returns JSON: `{"next": "exit"|"sched"|"info"|"respond", "user_message": "..."}`.
- **Exit Advisor** — `end` vs `dont_end`. Built with **prompt engineering**, not fine-tuning
  (the teacher changed this after an API change).
- **Sched Advisor** — `sched` vs `dont_sched`; if `sched`, retrieves 3 slots via SQLAlchemy.
- **Info Advisor** — `info_needed` vs `info_not_needed`; if needed, retrieves from the PDF.

Advisors receive the full chat history as a string. Only the Main Agent keeps `ChatMessageHistory`.
Evaluation labels are `continue` | `schedule` | `end`, and when advisors disagree the priority is
**end > schedule > continue**. Never offer slots after a clear opt-out.

## Branches

- `file_structure` — the study skeleton. Each file is a TODO stub with a `Help: Lesson N` line that
  must be preserved. Two students implement it themselves.
- `FINAL_PROJECT` — a complete working implementation, for **reference only**. Never copy it onto
  the study branch unless explicitly asked. Its Exit Advisor uses sklearn, which is now outdated.
- `main` — nearly empty original repo.

## Constraints

- Stay at the course technical level: plain Python modules, SQLAlchemy + SQLite, OpenAI,
  LangChain agents/tools/memory, simple Streamlit. Do not build a production system.
- LangChain is pinned to 0.3.x because the course uses `create_openai_tools_agent` and
  `AgentExecutor`, which were removed in 1.x. Do not upgrade.
- Orchestration is a plain Python loop, not LangGraph.
- Model: `gpt-4o` via `OPENAI_MODEL`, `ChatOpenAI(temperature=0)`.
- Not in scope: OpenAI fine-tuning, LangGraph, FastAPI, SQL Server, booking write-back
  (`UPDATE available=0`), multi-page Streamlit, renaming modules to the generic `module_1` template.

## Data and calendar

- The seed calendar is **2024**, Tuesday–Friday plus Sunday, 09:00–17:00. There are no Monday or
  Saturday rows. If a candidate asks for Monday, return the next real available slots and never
  invent times. Default position is `Python Dev`.
- Schedule access is retrieve-only. `date` and `time` are stored as TEXT (`YYYY-MM-DD`, `HH:MM:SS`)
  so SQLite sorts them correctly.
- The Streamlit UI must be able to simulate a 2024 date, since a real 2026 `now()` finds no slots.

## Conventions

- Run modules from the repo root: `python -m app.modules.embedding.embed_pdf`.
  Streamlit: `streamlit run streamlit_app/streamlit_main.py`.
- Shared paths live in `app/modules/config.py`, resolved from `Path(__file__).resolve().parents[2]`.
- Prompts are `.txt` files under `app/modules/prompts/` following Identity / Instructions / Examples.
  Escape literal `{` and `}` as `{{` `}}`, or `ChatPromptTemplate` reads them as input variables.
- Seeding uses a fixed random seed for reproducibility.

## Repo hygiene

- `assets/` is course material and is gitignored. Nothing in the project may depend on committing it.
- Never commit API keys. `.env` is gitignored; `.env.example` holds only a placeholder.
- Commit only when asked, push only when asked. No force push, no `--no-verify`.
- Commit messages are short, one sentence, and explain why.
