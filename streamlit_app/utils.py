"""Small Streamlit helpers."""

from datetime import datetime

OPENING_MESSAGE = (
    "Hi, thanks for submitting your application for our Python Developer role. "
    "Could you share a bit about your Python experience?"
)


def parse_simulated_date(value):
    if value is None:
        return datetime.now()
    if isinstance(value, datetime):
        return value
    return datetime.combine(value, datetime.min.time().replace(hour=9))


def registration_message(name, note):
    parts = []
    if name:
        parts.append(f"My name is {name}.")
    if note:
        parts.append(note)
    return " ".join(parts).strip()
