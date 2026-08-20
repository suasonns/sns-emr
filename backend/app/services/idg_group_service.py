# services/idg_group_service.py
"""
IDG Group management + fully-automatic recurring meeting generation.

See app/models/IDG_DOMAIN_MODEL.md for the 3-entity IDG domain model.
This service owns a 4th, purely scheduling-support concept:

    IDGGroup              — a named/numbered cohort of patients
    IDGGroupScheduleRule   — that cohort's recurring cadence (one or more
                             weekday rules, optionally restricted to
                             specific nth-occurrences-in-month)

Fully automatic: there is no "click to create" step. A scheduled job
(see run_automatic_idg_generation) computes every active group's next
occurrence(s) and creates IDGMeeting rows for every patient currently
assigned to that group.
"""

from __future__ import annotations

import calendar
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.idg_group import IDGGroup
from app.models.idg_group_schedule_rule import IDGGroupScheduleRule
from app.models.idg_meeting import IDGMeeting
from app.models.patient import Patient
from app.services.idg_meeting_scheduler import _as_aware_utc


class IDGGroupError(Exception):
    pass


# ---------------------------------------------------------------------
# Group CRUD
# ---------------------------------------------------------------------

def list_groups(db: Session, *, tenant_id) -> list[IDGGroup]:
    return (
        db.query(IDGGroup)
        .filter(IDGGroup.tenant_id == tenant_id)
        .order_by(IDGGroup.sort_order, IDGGroup.name)
        .all()
    )


def create_group(db: Session, *, tenant_id, name: str, created_by=None, sort_order: int = 0) -> IDGGroup:
    existing = (
        db.query(IDGGroup)
        .filter(IDGGroup.tenant_id == tenant_id, IDGGroup.name == name)
        .first()
    )
    if existing:
        raise IDGGroupError(f"A group named '{name}' already exists")
    group = IDGGroup(
        tenant_id=tenant_id,
        name=name,
        sort_order=sort_order,
        created_by=created_by,
    )
    db.add(group)
    db.commit()
    db.refresh(group)
    return group


def set_group_active(db: Session, *, tenant_id, group_id, is_active: bool) -> IDGGroup:
    group = (
        db.query(IDGGroup)
        .filter(IDGGroup.id == group_id, IDGGroup.tenant_id == tenant_id)
        .first()
    )
    if not group:
        raise IDGGroupError("IDG group not found")
    group.is_active = is_active
    db.commit()
    db.refresh(group)
    return group


# ---------------------------------------------------------------------
# Schedule rule CRUD
# ---------------------------------------------------------------------

def list_rules_for_group(db: Session, *, tenant_id, group_id) -> list[IDGGroupScheduleRule]:
    return (
        db.query(IDGGroupScheduleRule)
        .filter(
            IDGGroupScheduleRule.tenant_id == tenant_id,
            IDGGroupScheduleRule.idg_group_id == group_id,
        )
        .all()
    )


def add_schedule_rule(
    db: Session,
    *,
    tenant_id,
    group_id,
    weekday: int,
    nth_occurrences: Optional[list[int]] = None,
    created_by=None,
) -> IDGGroupScheduleRule:
    if not (0 <= weekday <= 6):
        raise IDGGroupError("weekday must be 0 (Monday) through 6 (Sunday)")
    if nth_occurrences is not None:
        for n in nth_occurrences:
            if n < 1 or n > 5:
                raise IDGGroupError("nth_occurrences values must be between 1 and 5")

    group = (
        db.query(IDGGroup)
        .filter(IDGGroup.id == group_id, IDGGroup.tenant_id == tenant_id)
        .first()
    )
    if not group:
        raise IDGGroupError("IDG group not found")

    rule = IDGGroupScheduleRule(
        tenant_id=tenant_id,
        idg_group_id=group_id,
        weekday=weekday,
        nth_occurrences=nth_occurrences,
        created_by=created_by,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def deactivate_schedule_rule(db: Session, *, tenant_id, rule_id) -> IDGGroupScheduleRule:
    rule = (
        db.query(IDGGroupScheduleRule)
        .filter(IDGGroupScheduleRule.id == rule_id, IDGGroupScheduleRule.tenant_id == tenant_id)
        .first()
    )
    if not rule:
        raise IDGGroupError("Schedule rule not found")
    rule.is_active = False
    db.commit()
    db.refresh(rule)
    return rule


# ---------------------------------------------------------------------
# Patient assignment
# ---------------------------------------------------------------------

def assign_patients_to_group(db: Session, *, tenant_id, group_id, patient_ids: list) -> int:
    group = (
        db.query(IDGGroup)
        .filter(IDGGroup.id == group_id, IDGGroup.tenant_id == tenant_id)
        .first()
    )
    if not group:
        raise IDGGroupError("IDG group not found")

    updated = (
        db.query(Patient)
        .filter(Patient.tenant_id == tenant_id, Patient.id.in_(patient_ids))
        .update({Patient.idg_group_id: group_id}, synchronize_session=False)
    )
    db.commit()
    return updated


def auto_split_unassigned_patients(db: Session, *, tenant_id, group_ids: list, mr_number_field="mrn") -> dict:
    """
    Convenience helper mirroring HospiceMD's "Odd only / Even only" MR#
    filter: evenly distributes every currently-unassigned active patient
    across the given groups by the last digit of their MRN.
    """
    if not group_ids:
        raise IDGGroupError("At least one group_id is required")

    patients = (
        db.query(Patient)
        .filter(
            Patient.tenant_id == tenant_id,
            Patient.status == "ACTIVE",
            Patient.idg_group_id.is_(None),
        )
        .all()
    )

    assigned_counts = {str(g): 0 for g in group_ids}
    for patient in patients:
        digits = "".join(ch for ch in (patient.mrn or "") if ch.isdigit())
        index = int(digits[-1]) % len(group_ids) if digits else 0
        group_id = group_ids[index % len(group_ids)]
        patient.idg_group_id = group_id
        assigned_counts[str(group_id)] += 1

    db.commit()
    return assigned_counts


# ---------------------------------------------------------------------
# Automatic recurring-date computation + generation
# ---------------------------------------------------------------------

def _nth_weekday_dates_in_month(year: int, month: int, weekday: int) -> list[datetime]:
    """All calendar dates in a given month matching `weekday`, in order
    (1st occurrence, 2nd occurrence, ...)."""
    cal = calendar.Calendar()
    return [
        datetime(year, month, day, tzinfo=timezone.utc)
        for day in [d for d in cal.itermonthdays(year, month) if d != 0]
        if datetime(year, month, day).weekday() == weekday
    ]


def compute_rule_dates(rule: IDGGroupScheduleRule, *, start_date: datetime, end_date: datetime) -> list[datetime]:
    """Every calendar date matching this single rule within [start_date, end_date]."""
    start_date = _as_aware_utc(start_date)
    end_date = _as_aware_utc(end_date)
    dates: list[datetime] = []

    year, month = start_date.year, start_date.month
    while (year, month) <= (end_date.year, end_date.month):
        month_dates = _nth_weekday_dates_in_month(year, month, rule.weekday)
        if rule.nth_occurrences:
            month_dates = [d for i, d in enumerate(month_dates, start=1) if i in rule.nth_occurrences]
        dates.extend(d for d in month_dates if start_date <= d <= end_date)

        if month == 12:
            year, month = year + 1, 1
        else:
            month += 1

    return sorted(dates)


def compute_group_dates(db: Session, *, tenant_id, group_id, start_date: datetime, end_date: datetime) -> list[datetime]:
    rules = [
        r
        for r in list_rules_for_group(db, tenant_id=tenant_id, group_id=group_id)
        if r.is_active
    ]
    all_dates: set = set()
    for rule in rules:
        all_dates.update(compute_rule_dates(rule, start_date=start_date, end_date=end_date))
    return sorted(all_dates)


def run_automatic_idg_generation(
    db: Session,
    *,
    tenant_id,
    horizon_days: int = 14,
    created_by=None,
) -> dict:
    """
    Fully automatic generation: for every active IDGGroup in the tenant,
    compute its upcoming meeting date(s) within the next `horizon_days`
    (per its IDGGroupScheduleRule set) and create an IDGMeeting row for
    every patient currently assigned to that group — idempotent by
    (tenant_id, patient_id, meeting_date), matching
    idg_meeting_scheduler.generate_idg_meetings's existing uniqueness
    behavior.

    Intended to run on a recurring schedule (e.g. nightly) — no manual
    "create meeting" click required.
    """
    now = datetime.now(timezone.utc)
    horizon_end = now + timedelta(days=horizon_days)

    groups = (
        db.query(IDGGroup)
        .filter(IDGGroup.tenant_id == tenant_id, IDGGroup.is_active.is_(True))
        .all()
    )

    created_count = 0
    results = []
    for group in groups:
        dates = compute_group_dates(db, tenant_id=tenant_id, group_id=group.id, start_date=now, end_date=horizon_end)
        if not dates:
            continue

        patients = (
            db.query(Patient)
            .filter(
                Patient.tenant_id == tenant_id,
                Patient.idg_group_id == group.id,
                Patient.status == "ACTIVE",
            )
            .all()
        )

        for meeting_date in dates:
            for patient in patients:
                existing = (
                    db.query(IDGMeeting)
                    .filter(
                        IDGMeeting.tenant_id == tenant_id,
                        IDGMeeting.patient_id == patient.id,
                        IDGMeeting.meeting_date == meeting_date,
                    )
                    .first()
                )
                if existing:
                    continue
                meeting = IDGMeeting(
                    tenant_id=tenant_id,
                    patient_id=patient.id,
                    meeting_date=meeting_date,
                    status="SCHEDULED",
                    created_by=created_by,
                )
                db.add(meeting)
                created_count += 1

        results.append(
            {
                "group_id": str(group.id),
                "group_name": group.name,
                "dates": [d.isoformat() for d in dates],
                "patient_count": len(patients),
            }
        )

    db.commit()
    return {"created_count": created_count, "groups": results}
