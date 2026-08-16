# RecruitAI

A student proof of concept for a multi-agent recruiting chatbot. The bot talks to a Python Developer candidate in Streamlit, answers questions from the job-description PDF, offers interview times from a local SQLite schedule, and ends the chat when the candidate is done or not interested.

This project uses the same level of tools taught in the course: Python modules, SQLAlchemy, sklearn tuning, OpenAI, LangChain agents/tools/memory, and a simple Streamlit UI.

## How to install and run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Put your OpenAI key in `.env`:

```
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o
```

Prepare local data (run these from the project root):

```bash
python data/seed_schedule.py
python -m app.modules.embedding.embed_pdf
python -m app.modules.finetuning.train_exit_model
```

Start the chat app:

```bash
streamlit run streamlit_app/streamlit_main.py
```

Or use the terminal debugger:

```bash
python -m app.main
```

Run tests:

```bash
python -m unittest tests.test_main
```

Open `tests/test_evals.ipynb` to compute accuracy and a confusion matrix on the labeled recruiter turns.

## Basic usage

1. The assistant starts with a short recruiter greeting.
2. Ask about the role (stack, skills, remote/hybrid). The Info Advisor searches the PDF.
3. Say you want to book a time. The Scheduling Advisor reads the chat, uses the conversation date, and offers the 3 nearest available Python Dev slots.
4. If you say you are not interested, the Exit Advisor ends the conversation.

The sidebar can simulate a 2024 conversation date so the seeded calendar still has slots. You can also send an optional name/note as the first candidate message.

## Project structure

```
RecruitAI/
  .gitignore
  README.md
  LICENSE
  requirements.txt
  .env
  data/                      # conversations, PDF, SQLite seed
  chroma_db/                 # created by the embedding step
  models/                    # created by Exit Advisor training
  app/
    main.py                  # CLI entry point
    modules/
      agents/                # Main Agent, advisors, orchestrator
      database/              # SQLAlchemy schedule queries
      embedding/             # PDF -> Chroma
      finetuning/            # labeled data + GridSearchCV
      prompts/               # role / instruction / few-shot prompts
  streamlit_app/
    streamlit_main.py
    utils.py
  tests/
    test_main.py
    test_evals.ipynb
```

`assets/` is course reference material only and is not part of the submitted app.

## Streamlit Community Cloud

- Add `OPENAI_API_KEY` as a secret.
- Set the main file to `streamlit_app/streamlit_main.py`.
- After deploy, run the seed / embed / train commands in the app environment, or add a one-time setup step. SQLite and Chroma files are local and may need to be rebuilt on a fresh container.

## Notes

- The original `db_Tech.sql` seed was SQL Server. This app uses SQLite with the same columns and calendar rules (2024, Tue–Fri and Sunday, 09:00–17:00).
- The seed has no Mondays. If a candidate asks for Monday, the tool returns the next real available slots.
- The Exit Advisor is a tuned sklearn model (Lesson 15 GridSearchCV), not an OpenAI fine-tuned LLM.
