"""Tests that do not need the OpenAI API."""
# Help: Lesson 16 - Sql & Python (DL) - Group By & Ddl & SqlAlchemy
# Help: Lesson 5 - Python - Pandas
# Help: Lesson 23 - GenAI - NLP & Embedding & Retrieval

import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import select

from app.modules.config import CHROMA_DIR, PDF_PATH, PROMPTS_DIR
from app.modules.database.db import engine, format_slots, get_nearest_slots, schedule
from app.modules.embedding.embed_pdf import retrieve_job_info
from app.modules.agents.orchestrator import resolve_action
from app.modules.agents import main_agent
from app.modules.evaluation.prepare_data import VALID_LABELS, build_labeled_rows
from streamlit_app.utils import OPENING_MESSAGE, parse_simulated_date, registration_message


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


class EmbedPdfTests(unittest.TestCase):
    def test_job_pdf_exists(self):
        self.assertTrue(PDF_PATH.exists(), f"expected job PDF at {PDF_PATH}")

    def test_missing_index_explains_how_to_build_it(self):
        # Empty folder on purpose — no embedding API call happens on this path.
        empty_dir = Path(tempfile.mkdtemp())
        message = retrieve_job_info("Is the role remote?", persist_dir=empty_dir)
        self.assertIn("embed_pdf", message)

    def test_chroma_dir_exists_after_embedding(self):
        self.assertTrue(
            CHROMA_DIR.exists() and any(CHROMA_DIR.iterdir()),
            "chroma_db/ is missing. Run: python -m app.modules.embedding.embed_pdf",
        )


class InfoAdvisorPromptTests(unittest.TestCase):
    def test_prompt_covers_both_decisions(self):
        text = (PROMPTS_DIR / "info_advisor.txt").read_text(encoding="utf-8")
        self.assertIn("info_needed", text)
        self.assertIn("info_not_needed", text)
        self.assertIn("retrieve_job_info", text)


class ExitAdvisorPromptTests(unittest.TestCase):
    def test_prompt_covers_both_decisions(self):
        text = (PROMPTS_DIR / "exit_advisor.txt").read_text(encoding="utf-8")
        self.assertIn('"decision": "end"', text)
        self.assertIn('"decision": "dont_end"', text)
        self.assertIn("not interested", text)
        self.assertIn("already accepted an offer", text)

    def test_predict_shape_defaults_are_documented(self):
        # Offline: only check the module contract, not a live LLM call.
        from app.modules.agents import exit_advisor

        self.assertEqual(exit_advisor.VALID_DECISIONS, {"end", "dont_end"})
        self.assertTrue(callable(exit_advisor.predict))


class ResolveActionTests(unittest.TestCase):
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

    def test_continue_when_no_advisors_ran(self):
        # This is the bug the two-step Main Agent prevents in handle_turn.
        action = resolve_action({"exit": None, "sched": None, "info": None})
        self.assertEqual(action, "continue")


class MainAgentPromptTests(unittest.TestCase):
    def test_advisor_prompt_lists_three_advisors(self):
        text = (PROMPTS_DIR / "main_agent_advisor.txt").read_text(encoding="utf-8")
        self.assertIn('"advisor": "exit"', text)
        self.assertIn('"advisor": "sched"', text)
        self.assertIn('"advisor": "info"', text)

    def test_reply_prompt_has_both_next_steps(self):
        text = (PROMPTS_DIR / "main_agent_reply.txt").read_text(encoding="utf-8")
        self.assertIn('"next": "consult_again"', text)
        self.assertIn('"next": "respond"', text)

    def test_format_history_messages(self):
        class FakeMessage:
            def __init__(self, type, content):
                self.type = type
                self.content = content

        text = main_agent.format_history_messages(
            [FakeMessage("human", "Hi"), FakeMessage("ai", "Hello")]
        )
        self.assertEqual(text, "Human: Hi\nAi: Hello")


class StreamlitUtilsTests(unittest.TestCase):
    def test_opening_message_mentions_python_role(self):
        self.assertIn("Python Developer", OPENING_MESSAGE)

    def test_registration_message_combines_name_and_note(self):
        text = registration_message("Majd", "I like Django.")
        self.assertEqual(text, "My name is Majd. I like Django.")

    def test_registration_message_empty_when_blank(self):
        self.assertEqual(registration_message("", ""), "")

    def test_parse_simulated_date_other_day_starts_at_nine(self):
        other = datetime(2026, 9, 15).date()
        parsed = parse_simulated_date(other)
        self.assertEqual(parsed.hour, 9)
        self.assertEqual(parsed.date(), other)


class PrepareDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frame = build_labeled_rows()

    def test_labels_are_only_continue_schedule_end(self):
        labels = set(self.frame["label"].unique())
        self.assertTrue(labels.issubset(VALID_LABELS))

    def test_expected_row_count_and_balance(self):
        self.assertEqual(len(self.frame), 59)
        counts = self.frame["label"].value_counts().to_dict()
        self.assertEqual(counts.get("continue"), 25)
        self.assertEqual(counts.get("schedule"), 19)
        self.assertEqual(counts.get("end"), 15)

    def test_required_columns_exist(self):
        for column in ("conversation_id", "turn_id", "timestamp_utc", "history", "label"):
            self.assertIn(column, self.frame.columns)

    def test_history_is_text_before_the_labeled_turn(self):
        # First labeled turn of a conversation often has empty history.
        first = self.frame.iloc[0]
        self.assertIsInstance(first["history"], str)


if __name__ == "__main__":
    unittest.main()
