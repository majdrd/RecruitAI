"""Create data/tech_schedule.db with the same Schedule rules as db_Tech.sql."""

import random
import sqlite3
import sys
from datetime import date, datetime, time, timedelta
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent
DB_PATH = DATA_DIR / "tech_schedule.db"

# Rolling twelve months from the run date, so a real datetime.now() always finds slots.
START_DATE = date.today()
END_DATE = START_DATE + timedelta(days=365)
SKIP_WEEKDAYS = {0, 5}  # Monday, Saturday
HOURS = list(range(9, 18))  # 09:00 through 17:00
POSITIONS = ["Python Dev", "Sql Dev", "Analyst", "ML"]


def iter_valid_dates():
    current = START_DATE
    while current <= END_DATE:
        if current.weekday() not in SKIP_WEEKDAYS:
            yield current
        current += timedelta(days=1)


def build_rows(rng):
    rows = []
    for day in iter_valid_dates():
        for hour in HOURS:
            for position in POSITIONS:
                available = 1 if rng.random() >= 0.5 else 0
                rows.append(
                    (
                        day.isoformat(),
                        time(hour, 0).strftime("%H:%M:%S"),
                        position,
                        available,
                    )
                )
    return rows


def seed(db_path=DB_PATH, seed=42):
    rng = random.Random(seed)
    rows = build_rows(rng)

    if db_path.exists():
        db_path.unlink()

    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    cursor.execute(
        """
        CREATE TABLE Schedule (
            ScheduleID INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            position VARCHAR(20) NOT NULL,
            available INTEGER NOT NULL
        )
        """
    )
    cursor.executemany(
        "INSERT INTO Schedule (date, time, position, available) VALUES (?, ?, ?, ?)",
        rows,
    )
    connection.commit()

    cursor.execute("SELECT COUNT(*) FROM Schedule")
    total = cursor.fetchone()[0]
    cursor.execute(
        """
        SELECT COUNT(*) FROM Schedule
        WHERE strftime('%w', date) IN ('1', '6')
        """
    )
    monday_saturday = cursor.fetchone()[0]
    connection.close()

    print(f"Created {db_path}")
    print(f"Inserted {total} rows")
    print(f"Monday/Saturday rows (should be 0): {monday_saturday}")
    print(f"Seeded at {datetime.now().isoformat(timespec='seconds')}")
    return total


if __name__ == "__main__":
    seed()
    sys.exit(0)
