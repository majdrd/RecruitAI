<!-- PROJECT LOGO -->
<p align="center">
  <img src="docs/images/logo/README LOGO.png" alt="RecruitAI logo" width="140">
</p>

<h1 align="center">RecruitAI</h1>

<p align="center">
  A multi-agent recruiting chatbot that answers job questions, offers interview slots, and knows when to stop<br>
  <a href="#usage">View Demo</a>
  ·
  <a href="https://github.com/majdrd/RecruitAI/issues">Report Bug</a>
  ·
  <a href="https://github.com/majdrd/RecruitAI/issues">Request Feature</a>
</p>

---
<br></br>

## Table of Contents

- [About The Project](#about-the-project)
- [Features](#features)
- [Getting Started](#getting-started)
- [Usage](#usage)
- [Screenshots](#screenshots)
- [Code Examples](#code-examples)
- [Project Structure](#project-structure)
- [To-Do List](#to-do-list)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)
- [Acknowledgments](#acknowledgments)

---
<br></br>


## About The Project

> RecruitAI is a proof-of-concept recruiting assistant that holds a conversation with a candidate
> who applied for a Python Developer role. It answers questions about the job from the official job
> description using retrieval, proposes real interview slots from a database, and ends the
> conversation politely when the candidate is no longer interested.

A **Main Agent** owns the conversation and its memory. It never touches the database or the vector
store directly. Each turn it makes two decisions: first it picks one of three specialised advisors,
then, once that advisor has answered, it either consults another advisor or writes the reply. It
never answers the candidate without consulting at least one advisor, and it stops after three.

```mermaid
flowchart LR
    Candidate[Candidate] --> MainAgent[Main Agent + memory]
    MainAgent -->|picks one| ExitAdvisor[Exit Advisor]
    MainAgent -->|picks one| SchedAdvisor[Sched Advisor]
    MainAgent -->|picks one| InfoAdvisor[Info Advisor]
    SchedAdvisor -->|SQL retrieve| Schedule[(SQLite Schedule)]
    InfoAdvisor -->|vector retrieve| Chroma[(Chroma - job description)]
    ExitAdvisor --> Decide{"Consult again or reply?"}
    SchedAdvisor --> Decide
    InfoAdvisor --> Decide
    Decide -->|consult again| MainAgent
    Decide -->|reply| Reply[Reply to candidate]
```

Each advisor returns a decision, never candidate-facing text. The Exit Advisor answers `end` or
`dont_end`, the Sched Advisor answers `sched` or `dont_sched` and retrieves the three nearest
available slots, and the Info Advisor answers whether the question needs the job description. When
advisors disagree, the priority is **end > schedule > continue**.

<div style="background: #272822; color: #f8f8f2; padding: 10px; border-radius: 8px;">
  <b> Technologies:</b> Python, LangChain, OpenAI API, Chroma, SQLAlchemy, SQLite, Pandas, Streamlit
</div>

---
<br></br>


## Features

- [x] Multi-agent orchestration with a Python control layer
- [x] Conversation memory on the Main Agent
- [x] Retrieval-augmented answers from a PDF job description (Chroma)
- [x] Interview slot lookup from a seeded SQLite calendar
- [x] Exit detection through prompt engineering
- [x] Evaluation against labelled recruiter conversations
- [x] Streamlit chat interface
- [ ] Cloud deployment _(coming soon!)_

---
<br></br>


##  Getting Started

### Prerequisites

- Python 3.12
- pip
- An OpenAI API key

### Installation

```bash
git clone https://github.com/majdrd/RecruitAI.git
cd RecruitAI
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Then put your OpenAI key in `.env`:

```bash
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o
```

---
<br></br>


## Usage

Build the interview calendar and the vector store once, then start the chat:

```bash
python data/seed_schedule.py
python -m app.modules.embedding.embed_pdf
streamlit run streamlit_app/streamlit_main.py
```

Run the tests that do not need the API:

```bash
python -m unittest discover -s tests -p "test_main.py"
```

> The seed script builds a **rolling 12 months of slots starting the day you run it**, so the app
> works with today's date out of the box. There are no Monday or Saturday slots. Reseed if the
> database is more than a year old.

---
<br></br>


## Screenshots

Run the Streamlit app locally to try the chat UI:

```bash
streamlit run streamlit_app/streamlit_main.py
```

_Optional: add saved screenshots under `docs/images/screenshots/` and link them here._

---
<br></br>


## Code Examples

Ask the schedule for the next three available interview slots:

```python
from datetime import datetime
from app.modules.database.db import get_nearest_slots

slots = get_nearest_slots(datetime.now(), position="Python Dev", limit=3)
for slot in slots:
    print(slot["date"], slot["time"])
```

Handle one conversation turn through the orchestrator:

```python
from app.modules.agents.orchestrator import handle_turn

result = handle_turn("Sorry, I'm not interested.", session_id="demo")
print(result["action"])   # end
print(result["message"])
```

---
<br></br>


## Project Structure

```text
RecruitAI/
├── app/
│   ├── main.py
│   └── modules/
│       ├── agents/            # main agent, exit / sched / info advisors, orchestrator
│       ├── database/          # SQLAlchemy access to the Schedule table
│       ├── embedding/         # PDF loading, chunking, Chroma vector store
│       ├── evaluation/        # labelled conversations prepared for scoring
│       ├── prompts/           # prompt files (Identity / Instructions / Examples)
│       └── config.py          # shared paths and environment loading
├── data/
│   ├── Python_Developer_Job_Description.pdf
│   ├── sms_conversations.json
│   └── seed_schedule.py
├── streamlit_app/
│   └── streamlit_main.py
├── docs/
│   └── images/                # logo, contributor photos, optional screenshots
├── tests/
│   ├── test_main.py
│   └── test_evals.ipynb
├── requirements.txt
├── .env.example
├── CONTRIBUTING.md
└── README.md
```

---
<br></br>


## To-Do List

- [x] Project structure and study skeleton
- [x] Exit Advisor switched from fine-tuning to prompt engineering
- [x] Schedule database and slot retrieval
- [x] PDF embedding and job-information retrieval
- [x] Advisors and Main Agent
- [x] Streamlit interface
- [x] Evaluation notebook
- [ ] Cloud deployment _(optional)_

---
<br></br>


## Contributing

This is a two-person student project. See [CONTRIBUTING.md](CONTRIBUTING.md) for the work split and
the rules for implementing the skeleton.

---
<br></br>


## License

Distributed under the MIT License. See `LICENSE` for more information.

---
<br></br>


## Contact

Built by two product developers as a GenAI course final project.

<table>
  <tr>
    <td align="center" width="50%">
      <img src="docs/images/contributors/majd-rada.jpg" width="140" height="140" alt="Majd Rada" style="border-radius: 50%;" /><br /><br />
      <b>Majd Rada</b><br />
      <sub>Product Developer · 11+ years</sub><br />
      <a href="mailto:majd.rd@gmail.com">majd.rd@gmail.com</a>
    </td>
    <td align="center" width="50%">
      <img src="docs/images/contributors/malak-abu-saleh.jpg" width="140" height="140" alt="Malak Abu Saleh" style="border-radius: 50%;" /><br /><br />
      <b>Malak Abu Saleh</b><br />
      <sub>Product Developer · 9+ years</sub><br />
      <a href="mailto:malakabusaleh96@gmail.com">malakabusaleh96@gmail.com</a>
    </td>
  </tr>
</table>

<p align="center">
  Project Link: <a href="https://github.com/majdrd/RecruitAI">github.com/majdrd/RecruitAI</a>
</p>


---
<br></br>


## Acknowledgments

- [Python](https://www.python.org/)
- [LangChain](https://python.langchain.com/)
- [OpenAI API](https://platform.openai.com/docs/overview)
- [Chroma](https://www.trychroma.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [Streamlit](https://streamlit.io/)


---
