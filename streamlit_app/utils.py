"""Small Streamlit helpers."""
# Help: Lesson 3 - Python - Functions

from datetime import datetime
from pathlib import Path

OPENING_MESSAGE = (
    "Hi, thanks for submitting your application for our Python Developer role. "
    "Could you share a bit about your Python experience?"
)

# Blue-circle mascot works best on the dark blue UI theme.
LOGO_PATH = (
    Path(__file__).resolve().parents[1] / "docs" / "images" / "logo" / "README LOGO.png"
)
STYLES_PATH = Path(__file__).resolve().parent / "styles.css"


def load_css():
    """Read styles.css and wrap it for st.markdown."""
    css = STYLES_PATH.read_text(encoding="utf-8")
    return f"<style>\n{css}\n</style>"


def parse_simulated_date(value):
    """Turn the sidebar date into a datetime the Sched Advisor can use."""
    if value is None:
        return datetime.now()
    if isinstance(value, datetime):
        return value

    now = datetime.now()
    if value == now.date():
        return now
    # Other days: start looking from 09:00 on that day.
    return datetime.combine(value, datetime.min.time().replace(hour=9))


def registration_message(name, note):
    """Build the first user message from optional name / note fields."""
    parts = []
    if name:
        parts.append(f"My name is {name}.")
    if note:
        parts.append(note)
    return " ".join(parts).strip()
