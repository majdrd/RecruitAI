# RecruitAI (study skeleton)

This branch is the **empty file structure** for learning. Each code file has a TODO and a **Help: Lesson N** line. Fill in the files yourself. The finished solution lives on the `FINAL_PROJECT` branch if you get stuck.

This layout follows the teacher template (`app/`, `streamlit_app/`, `tests/`) with real module names (Fine-Tuning, Embedding, agents). The brief allows that adjustment.

## How to install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Put your OpenAI key in `.env`.

Suggested order after you implement the matching files:

```bash
python data/seed_schedule.py
python -m app.modules.embedding.embed_pdf
python -m app.modules.finetuning.train_exit_model
streamlit run streamlit_app/streamlit_main.py
```

## Suggested split

**Person A**

- `data/seed_schedule.py`
- `app/modules/database/db.py`
- `app/modules/agents/sched_advisor.py`
- `app/modules/prompts/sched_advisor.txt`

**Person B**

- `app/modules/embedding/embed_pdf.py`
- `app/modules/agents/info_advisor.py`
- `app/modules/prompts/info_advisor.txt`

**Together later**

- Exit model (`finetuning/` + `exit_advisor.py`)
- Main Agent + orchestrator
- Streamlit
- `tests/test_evals.ipynb`

## Project structure

```
RecruitAI/
  .gitignore
  README.md
  LICENSE
  requirements.txt
  .env.example
  data/                      # PDF, labeled chats, seed script
  models/                    # exit_advisor.pkl after training
  app/
    main.py
    modules/
      agents/
      database/
      embedding/
      finetuning/
      prompts/
  streamlit_app/
  tests/
```

`assets/` is course reference only and is gitignored.
