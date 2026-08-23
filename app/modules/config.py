"""Shared paths and environment loading."""

from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "tech_schedule.db"
PDF_PATH = DATA_DIR / "Python_Developer_Job_Description.pdf"
CONVERSATIONS_PATH = DATA_DIR / "sms_conversations.json"
CHROMA_DIR = PROJECT_ROOT / "chroma_db"
PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
DEFAULT_POSITION = "Python Dev"
DEFAULT_MODEL = "gpt-4o"
