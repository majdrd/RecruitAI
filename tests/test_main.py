"""Tests that do not need the OpenAI API."""
# Help: Lesson 16 - Sql & Python (DL) - Group By & Ddl & SqlAlchemy
# Help: Lesson 5 - Python - Pandas

import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import select

from app.modules.database.db import engine, format_slots, get_nearest_slots, schedule


class ScheduleTests(unittest.TestCase):
    def test_returns_at_most_the_limit(self):
        self.assertLessEqual(len(get_nearest_slots(datetime.now(), limit=3)), 3)
        self.assertLessEqual(len(get_nearest_slots(datetime.now(), limit=1)), 1)

    def test_slots_exist_and_are_ordered(self):
        slots = get_nearest_slots(datetime.now(), limit=3)
        self.assertTrue(slots, "the seeded database should have available Python Dev slots")
        stamps = [f"{slot['date']} {slot['time']}" for slot in slots]
        self.assertEqual(stamps, sorted(stamps))

    def test_no_monday_or_saturday(self):
        # The seed skips weekday 0 (Monday) and 5 (Saturday), so no slot may fall on one.
        slots = get_nearest_slots(datetime.now(), limit=3)
        for slot in slots:
            weekday = datetime.strptime(slot["date"], "%Y-%m-%d").weekday()
            self.assertNotIn(weekday, (0, 5))

    def test_no_slots_past_the_calendar(self):
        beyond = datetime.now() + timedelta(days=400)
        self.assertEqual(get_nearest_slots(beyond), [])

    def test_never_returns_a_slot_before_the_requested_time(self):
        slots = get_nearest_slots(datetime.now(), limit=1)
        self.assertTrue(slots)
        first = slots[0]
        exact = datetime.strptime(f"{first['date']} {first['time']}", "%Y-%m-%d %H:%M")

        # Asking from exactly that moment still offers the slot.
        same = get_nearest_slots(exact, limit=1)
        self.assertEqual(same[0]["schedule_id"], first["schedule_id"])

        # Asking one minute later no longer offers it.
        later = get_nearest_slots(exact + timedelta(minutes=1), limit=1)
        self.assertNotEqual(later[0]["schedule_id"], first["schedule_id"])

    def test_position_filter(self):
        slots = get_nearest_slots(datetime.now(), position="Analyst", limit=3)
        self.assertTrue(slots)
        for slot in slots:
            self.assertEqual(slot["position"], "Analyst")

    def test_only_available_slots_are_returned(self):
        slots = get_nearest_slots(datetime.now(), limit=3)
        self.assertTrue(slots)
        ids = [slot["schedule_id"] for slot in slots]
        query = select(schedule.c.available).where(schedule.c.ScheduleID.in_(ids))
        with engine.connect() as connection:
            flags = [row.available for row in connection.execute(query)]
        self.assertEqual(set(flags), {1})


class FormatSlotsTests(unittest.TestCase):
    def test_says_so_when_there_is_nothing(self):
        self.assertIn("No available", format_slots([]))

    def test_numbers_each_option(self):
        slots = [
            {"schedule_id": 1, "date": "2026-09-01", "time": "09:00", "position": "Python Dev"},
            {"schedule_id": 2, "date": "2026-09-01", "time": "11:00", "position": "Python Dev"},
        ]
        text = format_slots(slots)
        self.assertIn("Option 1: 2026-09-01 at 09:00 (Python Dev)", text)
        self.assertIn("Option 2: 2026-09-01 at 11:00 (Python Dev)", text)
        self.assertEqual(len(text.splitlines()), 2)


if __name__ == "__main__":
    unittest.main()
