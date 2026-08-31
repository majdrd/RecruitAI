"""SQLAlchemy access to the interview Schedule table."""
# Help: Lesson 16 - Sql & Python (DL) - Group By & Ddl & SqlAlchemy (SQLAlchemy)

from datetime import datetime, time

from sqlalchemy import Column, Integer, MetaData, String, Table, and_, create_engine, or_, select

from app.modules.config import DB_PATH, DEFAULT_POSITION

engine = create_engine(f"sqlite:///{DB_PATH}")
metadata = MetaData()

# date and time are TEXT ("YYYY-MM-DD" and "HH:MM:SS") so SQLite sorts them correctly.
schedule = Table(
    "Schedule",
    metadata,
    Column("ScheduleID", Integer, primary_key=True),
    Column("date", String, nullable=False),
    Column("time", String, nullable=False),
    Column("position", String, nullable=False),
    Column("available", Integer, nullable=False),
)


def get_nearest_slots(after_dt, position=DEFAULT_POSITION, limit=3):
    """Return up to `limit` available slots on or after after_dt, earliest first."""
    if not isinstance(after_dt, datetime):
        after_dt = datetime.combine(after_dt, time.min)

    after_date = after_dt.strftime("%Y-%m-%d")
    after_time = after_dt.strftime("%H:%M:%S")

    # Either a later day, or the same day at or after the given time.
    not_in_the_past = or_(
        schedule.c.date > after_date,
        and_(schedule.c.date == after_date, schedule.c.time >= after_time),
    )

    query = (
        select(schedule)
        .where(and_(schedule.c.available == 1, schedule.c.position == position, not_in_the_past))
        .order_by(schedule.c.date, schedule.c.time)
        .limit(limit)
    )

    with engine.connect() as connection:
        rows = connection.execute(query).fetchall()

    slots = []
    for row in rows:
        slots.append(
            {
                "schedule_id": row.ScheduleID,
                "date": row.date,
                "time": row.time[:5],  # "HH:MM:SS" -> "HH:MM"
                "position": row.position,
            }
        )
    return slots


def format_slots(slots):
    """Turn slot dictionaries into short lines the Main Agent can quote."""
    if not slots:
        return "No available interview slots were found after that date."

    lines = []
    for index, slot in enumerate(slots, start=1):
        lines.append(f"Option {index}: {slot['date']} at {slot['time']} ({slot['position']})")
    return "\n".join(lines)
