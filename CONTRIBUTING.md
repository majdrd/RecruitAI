# Contributing

RecruitAI is a two-person student project by **Majd Rada** and **Malak Abu Saleh**. The `main` branch
is an **empty skeleton**: every code file holds a TODO describing what it should do and a
`Help: Lesson N` line pointing at the course lesson that teaches it. The point is to implement the
files yourself.

A finished reference implementation lives on the `FINAL_PROJECT` branch. Use it only if you are
stuck, and do not copy it over the skeleton.

## Ground rules

- Implementing a file means **replacing** its TODO stub with real code, not adding code underneath it.
- Keep the `Help: Lesson N` comment at the top of the file.
- Stay at the level of the course lessons. No extra frameworks.
- The Exit Advisor uses **prompt engineering**, not fine-tuning, following the teacher's update.
- Never commit `.env` or any API key.

See the [README](README.md) for the architecture diagram and the technical stack.

## Work split

**Majd Rada — scheduling**

- `data/seed_schedule.py`
- `app/modules/database/db.py`
- `app/modules/agents/sched_advisor.py`
- `app/modules/prompts/sched_advisor.txt`

**Malak Abu Saleh — job information**

- `app/modules/embedding/embed_pdf.py`
- `app/modules/agents/info_advisor.py`
- `app/modules/prompts/info_advisor.txt`

**Together, afterwards**

- Exit Advisor (`app/modules/prompts/exit_advisor.txt` + `app/modules/agents/exit_advisor.py`)
- Main Agent and orchestrator (two decisions, so two prompts: `main_agent_advisor.txt` and
  `main_agent_reply.txt`)
- Streamlit interface
- `tests/test_evals.ipynb`

Note that `app/modules/config.py` holds the shared paths that both halves import, so whoever starts
first should write it.

## Getting started

```bash
git fetch origin
git checkout main
git pull
source .venv/bin/activate
```

Work on a short-lived branch off `main` and open a pull request when the piece is done.

Course material under `assets/` is reference only and is gitignored, so nothing in the project may
depend on it.
