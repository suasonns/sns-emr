# services/bereavement_letters_service.py

"""
Support logic for the Bereavement Letters Tracker (chart-section-
bereavement-letters): stable item keys, dynamic per-item status computation,
and tracker seeding from the same CMS-aligned 13-month touchpoint schedule
used by the Bereavement POC (app/services/bereavement_poc_catalog.py) --
single source of truth for the schedule itself, kept separate from the
POC's own record so completions can keep being logged after the POC is
signed and locked.

CMS COP reference: 42 CFR 418.64(d) requires bereavement services be
available to the family/caregiver for at least 13 months following the
patient's death, per an individualized bereavement plan of care.
"""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta, timezone
from typing import Any

from app.services.bereavement_poc_catalog import default_action_plan

# An item due within this many days (inclusive) counts as "due soon" for
# alerting purposes, so staff get a heads-up before something becomes
# overdue rather than only being told after the fact.
DUE_SOON_WINDOW_DAYS = 7


def _slugify(label: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", label.strip().lower()).strip("_")
    return slug or "touchpoint"


def _iso(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return value.isoformat()


def build_default_items(risk_level: str | None, date_of_death: date | None) -> list[dict]:
    """
    Seed a tracker's items from the shared 13-month touchpoint schedule,
    adding a stable `key` (derived from offset + label, so it survives
    label wording tweaks across items) and the tracker-specific completion
    fields (sent_date/sent_method/sent_by) alongside the schedule fields
    already produced by default_action_plan().
    """
    plan = default_action_plan(risk_level, date_of_death)
    items: list[dict] = []
    for entry in plan:
        offset = entry["month_offset_days"]
        key = f"d{offset:04d}_{_slugify(entry['label'])}"
        items.append(
            {
                "key": key,
                "month_offset_days": offset,
                "label": entry["label"],
                "contact_type": entry["contact_type"],
                "required": entry["required"],
                "included": entry["included"],
                "due_date": entry["planned_date"],
                "sent_date": None,
                "sent_method": None,
                "sent_by": None,
                "notes": None,
            }
        )
    return items


def item_runtime_status(item: dict, today: date | None = None) -> str:
    """
    Computed (never persisted) status for a single item:
      SENT        - sent_date is set
      SKIPPED     - not included (clinician opted this touchpoint out)
      UNSCHEDULED - included but no due_date yet (date of death unknown)
      OVERDUE     - due_date in the past, not sent
      DUE_SOON    - due_date within DUE_SOON_WINDOW_DAYS, not sent
      UPCOMING    - due_date further out, not sent
    """
    if item.get("sent_date"):
        return "SENT"
    if not item.get("included", True):
        return "SKIPPED"

    due_raw = item.get("due_date")
    if not due_raw:
        return "UNSCHEDULED"

    due = due_raw if isinstance(due_raw, date) else date.fromisoformat(str(due_raw))
    today = today or datetime.now(timezone.utc).date()

    if due < today:
        return "OVERDUE"
    if due <= today + timedelta(days=DUE_SOON_WINDOW_DAYS):
        return "DUE_SOON"
    return "UPCOMING"


def summarize_items(items: list[dict], today: date | None = None) -> dict:
    """Tenant/board-level rollup counts used for list views and badges."""
    today = today or datetime.now(timezone.utc).date()
    counts = {"SENT": 0, "SKIPPED": 0, "UNSCHEDULED": 0, "OVERDUE": 0, "DUE_SOON": 0, "UPCOMING": 0}
    for item in items:
        counts[item_runtime_status(item, today)] += 1
    active_total = sum(1 for i in items if i.get("included", True))
    return {
        "total_items": len(items),
        "active_items": active_total,
        "sent_count": counts["SENT"],
        "overdue_count": counts["OVERDUE"],
        "due_soon_count": counts["DUE_SOON"],
        "upcoming_count": counts["UPCOMING"],
        "unscheduled_count": counts["UNSCHEDULED"],
        "skipped_count": counts["SKIPPED"],
        "complete": active_total > 0 and counts["SENT"] == active_total,
    }


def serialize_items_with_status(items: list[dict], today: date | None = None) -> list[dict]:
    today = today or datetime.now(timezone.utc).date()
    out = []
    for item in items:
        enriched = dict(item)
        enriched["status"] = item_runtime_status(item, today)
        out.append(enriched)
    return out
