from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Iterable


# ---------------------------------------------------------
# Locked POS defaults
# ---------------------------------------------------------

POS_DEFAULT_LOC_MAP = {
    "HOME": "ROUTINE",
    "AL": "ROUTINE",
    "B&C": "ROUTINE",
    "SNF": "ROUTINE",
    "HOSPITAL": "GIP",
    "LTC": "GIP",
    "HOSPICE FACILITY": "GIP",
}

# Continuous Care / CHC must never apply in SNF/HOSPITAL/LTC/HOSPICE FACILITY
CONTINUOUS_ALLOWED_POS = {"HOME", "AL", "B&C"}


@dataclass(frozen=True)
class DateRangeEvent:
    start_date: date
    end_date: date
    reason: str | None = None


def iter_dates(start_date: date, end_date: date) -> Iterable[date]:
    current = start_date
    while current <= end_date:
        yield current
        current += timedelta(days=1)


def normalize_pos(pos_type: str | None) -> str | None:
    if pos_type is None:
        return None
    return pos_type.strip().upper()


def build_pos_timeline(pos_records, start_date: date, end_date: date) -> list[dict]:
    """
    Builds one POS row per day.

    Expected pos_records items:
    - effective_date
    - end_date
    - pos_type
    - facility_name
    """
    timeline_by_date: dict[date, dict] = {}

    for record in pos_records:
        record_start = max(record.effective_date, start_date)
        record_end = min(record.end_date or end_date, end_date)
        pos_type = normalize_pos(record.pos_type)

        for day in iter_dates(record_start, record_end):
            timeline_by_date[day] = {
                "date": day,
                "pos": pos_type,
                "facility_name": getattr(record, "facility_name", None),
            }

    # Fill missing days with explicit None so billing can flag gaps
    result: list[dict] = []
    for day in iter_dates(start_date, end_date):
        result.append(
            timeline_by_date.get(
                day,
                {
                    "date": day,
                    "pos": None,
                    "facility_name": None,
                },
            )
        )

    return result


def _event_hits(day: date, events: list[DateRangeEvent]) -> bool:
    for event in events:
        if event.start_date <= day <= event.end_date:
            return True
    return False


def resolve_loc_for_day(
    day: date,
    pos_type: str | None,
    gip_events: list[DateRangeEvent],
    respite_events: list[DateRangeEvent],
    continuous_events: list[DateRangeEvent],
) -> str | None:
    """
    Priority rules (locked):
    1. CONTINUOUS CARE (only allowed in HOME / AL / B&C)
    2. GIP
    3. RESPITE
    4. POS default
    """
    pos_type = normalize_pos(pos_type)

    # 1) Continuous Care
    if (
        pos_type in CONTINUOUS_ALLOWED_POS
        and _event_hits(day, continuous_events)
    ):
        return "CONTINUOUS CARE"

    # 2) GIP
    if _event_hits(day, gip_events):
        return "GIP"

    # 3) Respite
    if _event_hits(day, respite_events):
        return "RESPITE"

    # 4) POS default
    return POS_DEFAULT_LOC_MAP.get(pos_type)


def build_loc_timeline(
    pos_timeline: list[dict],
    gip_events: list[DateRangeEvent],
    respite_events: list[DateRangeEvent],
    continuous_events: list[DateRangeEvent],
) -> list[dict]:
    """
    Output example:
    [
        {
            "date": date(2026, 5, 1),
            "pos": "HOME",
            "loc": "ROUTINE",
            "facility_name": None
        }
    ]
    """
    result: list[dict] = []

    for row in pos_timeline:
        day = row["date"]
        pos_type = row["pos"]

        resolved_loc = resolve_loc_for_day(
            day=day,
            pos_type=pos_type,
            gip_events=gip_events,
            respite_events=respite_events,
            continuous_events=continuous_events,
        )

        result.append(
            {
                "date": day,
                "pos": pos_type,
                "loc": resolved_loc,
                "facility_name": row.get("facility_name"),
            }
        )

    return result