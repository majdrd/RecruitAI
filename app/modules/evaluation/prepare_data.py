"""Turn labeled SMS conversations into a table for evaluation."""

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.modules.config import CONVERSATIONS_PATH, DATA_DIR


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
    if conversations is None:
        conversations = load_conversations()

    rows = []
    for conversation in conversations:
        turns = conversation["turns"]
        for index, turn in enumerate(turns):
            if turn["speaker"] != "recruiter" or not turn.get("label"):
                continue
            history_turns = turns[:index]
            label = turn["label"]
            rows.append(
                {
                    "conversation_id": conversation["conversation_id"],
                    "turn_id": turn["turn_id"],
                    "start_time_utc": conversation["start_time_utc"],
                    "timestamp_utc": turn["timestamp_utc"],
                    "history": format_turns(history_turns),
                    "label": label,
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
