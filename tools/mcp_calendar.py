from __future__ import annotations

from datetime import datetime, timedelta


def find_free_slots(
    duration_min: int = 60,
    day: str | None = None,
    start_hour: int = 9,
    end_hour: int = 21,
) -> list[str]:
    # Mock deterministic slots; this keeps demo behavior stable and predictable.
    if day:
        base = datetime.strptime(day, "%Y-%m-%d")
    else:
        now = datetime.now()
        base = datetime(now.year, now.month, now.day)

    if duration_min <= 0:
        duration_min = 60

    step_minutes = 30
    current = base.replace(hour=start_hour, minute=0, second=0, microsecond=0)
    finish = base.replace(hour=end_hour, minute=0, second=0, microsecond=0)

    slots: list[str] = []
    while current + timedelta(minutes=duration_min) <= finish:
        start = current
        end = current + timedelta(minutes=duration_min)
        slots.append(f"{start.isoformat()} to {end.isoformat()}")
        current += timedelta(minutes=step_minutes)

    if not slots:
        fallback_start = base.replace(hour=16, minute=0, second=0, microsecond=0)
        fallback_end = fallback_start + timedelta(minutes=duration_min)
        slots.append(f"{fallback_start.isoformat()} to {fallback_end.isoformat()}")

    return slots


def book_slot(task_title: str, slot: str) -> dict:
    return {
        "task_title": task_title,
        "slot": slot,
        "status": "booked",
        "provider": "mock_calendar",
    }
