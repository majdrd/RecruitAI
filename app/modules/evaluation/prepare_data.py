"""Turn labeled SMS conversations into a table for evaluation."""
# Help: Lesson 5 - Python - Pandas
# Help: Lesson 12 - ML - Eda & Pandas

import json

import pandas as pd

from app.modules.config import CONVERSATIONS_PATH, DATA_DIR

VALID_LABELS = {"continue", "schedule", "end"}


def load_conversations(path=CONVERSATIONS_PATH):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def format_turns(turns):
    lines = []
    for turn in turns:
        speaker = turn["speaker"].capitalize()
        lines.append(f"{speaker}: {turn['text']}")
    return "\n".join(lines)


def build_labeled_rows(conversations=None):
    """One row per labeled recruiter turn. history = all turns before it."""
    if conversations is None:
        conversations = load_conversations()

    rows = []
    for conversation in conversations:
        turns = conversation["turns"]
        for index, turn in enumerate(turns):
            if turn["speaker"] != "recruiter":
                continue
            if not turn.get("label"):
                continue

            history_turns = turns[:index]
            rows.append(
                {
                    "conversation_id": conversation["conversation_id"],
                    "turn_id": turn["turn_id"],
                    "timestamp_utc": turn["timestamp_utc"],
                    "history": format_turns(history_turns),
                    "label": turn["label"],
                }
            )
    return pd.DataFrame(rows)


def save_labeled_csv(output_path=None):
    if output_path is None:
        output_path = DATA_DIR / "labeled_turns.csv"

    frame = build_labeled_rows()
    frame.to_csv(output_path, index=False)
    print(f"Wrote {len(frame)} labeled recruiter turns to {output_path}")
    print(frame["label"].value_counts().to_string())
    return frame


if __name__ == "__main__":
    save_labeled_csv()
