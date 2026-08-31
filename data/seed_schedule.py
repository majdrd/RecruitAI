"""Create data/tech_schedule.db with the same Schedule rules as db_Tech.sql."""
# Help: Lesson 16 - Sql & Python (DL) - Group By & Ddl & SqlAlchemy (SQLite3 section)

import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "tech_schedule.db"
WORKING_HOURS = range(9, 18)  # 09:00 through 17:00
POSITIONS = ["Python Dev", "Sql Dev", "Analyst", "ML"]
SKIP_WEEKDAYS = (0, 5)  # 0 = Monday, 5 = Saturday: no interview slots on those days
RANDOM_SEED = 42


def create_database():
    # Fixed seed so every run produces the same available values.
    random.seed(RANDOM_SEED)

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    # Drop first, otherwise re-running the script appends a second copy of every row.
    cursor.execute("DROP TABLE IF EXISTS Schedule")
    cursor.execute("""
        CREATE TABLE Schedule (
            ScheduleID INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            position TEXT NOT NULL,
            available INTEGER NOT NULL
        )
    """)

    start_date = date.today()
    end_date = start_date + timedelta(days=365)

    current_date = start_date
    while current_date <= end_date:
        if current_date.weekday() not in SKIP_WEEKDAYS:
            for hour in WORKING_HOURS:
                for position in POSITIONS:
                    available = random.choice([0, 1])
                    cursor.execute(
                        "INSERT INTO Schedule (date, time, position, available) VALUES (?, ?, ?, ?)",
                        (current_date.isoformat(), f"{hour:02d}:00:00", position, available),
                    )
        current_date += timedelta(days=1)

    connection.commit()

    cursor.execute("SELECT COUNT(*) FROM Schedule")
    total = cursor.fetchone()[0]
    connection.close()

    print(f"Database created successfully at {DB_PATH}")
    print(f"Inserted {total} rows")


if __name__ == "__main__":
    create_database()
