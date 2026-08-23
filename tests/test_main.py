"""Tests that do not need the OpenAI API."""

import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.modules.agents.orchestrator import resolve_action
from app.modules.database.db import get_nearest_slots
from app.modules.evaluation.prepare_data import build_labeled_rows


class ScheduleTests(unittest.TestCase):
    def test_nearest_slots_limit_and_order(self):
        slots = get_nearest_slots(datetime.now(), position="Python Dev", limit=3)
        self.assertLessEqual(len(slots), 3)
        self.assertTrue(slots, "seeded database should have available Python Dev slots")
        dates = [slot["date"] for slot in slots]
        self.assertEqual(dates, sorted(dates))
        for slot in slots:
            weekday = datetime.strptime(slot["date"], "%Y-%m-%d").weekday()
            self.assertNotIn(weekday, {0, 5}, "Monday and Saturday should not appear")

    def test_no_slots_past_the_calendar(self):
        beyond = datetime.now() + timedelta(days=400)
        slots = get_nearest_slots(beyond, position="Python Dev", limit=3)
        self.assertEqual(slots, [])


class LabelTests(unittest.TestCase):
    def test_labeled_turns_have_expected_values(self):
        frame = build_labeled_rows()
        self.assertFalse(frame.empty)
        self.assertTrue(set(frame["label"]).issubset({"continue", "schedule", "end"}))
        expected_columns = {"conversation_id", "turn_id", "timestamp_utc", "history", "label"}
        self.assertTrue(expected_columns.issubset(frame.columns))
        self.assertNotIn("end_label", frame.columns)


class ActionPriorityTests(unittest.TestCase):
    def test_end_beats_schedule(self):
        action = resolve_action(
            {
                "exit": {"decision": "end"},
                "sched": {"decision": "sched"},
            }
        )
        self.assertEqual(action, "end")

    def test_schedule_when_not_ending(self):
        action = resolve_action(
            {
                "exit": {"decision": "dont_end"},
                "sched": {"decision": "sched"},
            }
        )
        self.assertEqual(action, "schedule")

    def test_continue_default(self):
        action = resolve_action(
            {
                "exit": {"decision": "dont_end"},
                "sched": {"decision": "dont_sched"},
            }
        )
        self.assertEqual(action, "continue")


if __name__ == "__main__":
    unittest.main()
