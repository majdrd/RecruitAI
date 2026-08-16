"""SQLAlchemy access to the interview Schedule table."""

from datetime import date, datetime, time

from sqlalchemy import (
    Column,
    Integer,
    MetaData,
    String,
    Table,
    and_,
    create_engine,
    or_,
    select,
)

from app.modules.config import DB_PATH, DEFAULT_POSITION

engine = create_engine(f"sqlite:///{DB_PATH}")
metadata = MetaData()

schedule = Table(
    "Schedule",
    metadata,
    Column("ScheduleID", Integer, primary_key=True),
    Column("date", String, nullable=False),
    Column("time", String, nullable=False),
    Column("position", String(20), nullable=False),
    Column("available", Integer, nullable=False),
)


def _as_datetime(value):
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, time.min)
    raise TypeError("after_dt must be a datetime or date")


def get_nearest_slots(after_dt, position=DEFAULT_POSITION, limit=3):
    """Return up to `limit` available slots on or after after_dt."""
    after_dt = _as_datetime(after_dt)
    after_date = after_dt.strftime("%Y-%m-%d")
    after_time = after_dt.strftime("%H:%M:%S")

    query = (
        select(schedule)
        .where(
            and_(
                schedule.c.available == 1,
                schedule.c.position == position,
                or_(
                    schedule.c.date > after_date,
                    and_(
                        schedule.c.date == after_date,
                        schedule.c.time >= after_time,
                    ),
                ),
            )
        )
        .order_by(schedule.c.date, schedule.c.time)
        .limit(limit)
    )

    with engine.connect() as connection:
        rows = connection.execute(query).fetchall()

    slots = []
    for row in rows:
        slot_time = str(row.time)[:5]
        slots.append(
            {
                "schedule_id": row.ScheduleID,
                "date": str(row.date),
                "time": slot_time,
                "position": row.position,
            }
        )
    return slots


def format_slots(slots):
    if not slots:
        return "No available interview slots were found after that date."
    lines = []
    for index, slot in enumerate(slots, start=1):
        lines.append(
            f"Option {index}: {slot['date']} at {slot['time']} ({slot['position']})"
        )
    return "\n".join(lines)
