"""
Supervisory-visit scheduling / compliance engine.

Computes CHHA (14-day) and LVN (28-day) RN-supervisory-visit due dates for a
patient, per the confirmed rules (visit_notes_scheduling_spec.md section 6):

- Week = Sunday-Saturday.
- SOC-week edge case: the partial calendar week containing SOC never owes an
  additional visit; "week 1" of the cadence always starts on the Sunday
  immediately after the SOC week ends (this generalizes the confirmed
  Saturday-SOC example to any SOC weekday).
- CHHA supervisory cadence = every 14 days. LVN supervisory cadence = every
  28 days. Both are satisfied by a single RN supervisory visit when the
  cycles coincide (28 = 2x14), so the LVN cadence is computed against the
  same effective start date.
- Only required when the patient has an active CHHA assignment (for the
  CHHA cadence) or an active LVN assignment (for the LVN cadence). If the
  patient has neither (RN-only care), no supervisory documentation is
  required at all and this returns "required": False for both.
- PRN/unscheduled visits (form_type == SHORT_FORM) never satisfy a
  supervisory cycle.

Scope note: this module computes and flags due/overdue supervisory
obligations. It does NOT auto-assign which specific future date an RN vs.
LVN staff member should visit (no rostering/auto-scheduling of individual
visits) -- that is a separate, unbuilt feature area.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.admission import Admission
from app.models.patient_assignment import PatientAssignment
from app.models.visit import Visit

# Visit statuses that do NOT count as evidence of a completed visit for
# compliance-cycle satisfaction purposes.
_NON_QUALIFYING_STATUSES = {"MISSED", "CANCELLED", "DRAFT"}

CHHA_CADENCE_DAYS = 14
LVN_CADENCE_DAYS = 28


@dataclass
class CycleResult:
    cycle_start: date
    cycle_end: date
    satisfied: bool
    satisfying_visit_id: Optional[str]
    satisfying_visit_date: Optional[date]


def _week_end_saturday(d: date) -> date:
    """Return the Saturday that ends the Sunday-Saturday week containing d."""
    # Python's date.weekday(): Monday=0 ... Sunday=6.
    # Days remaining until Saturday (weekday=5), counting Sunday as start-of-week.
    days_until_saturday = (5 - d.weekday()) % 7
    return d + timedelta(days=days_until_saturday)


def _effective_cadence_start(soc_date: date) -> date:
    """
    Week 1 of any supervisory cadence starts the Sunday immediately after the
    SOC calendar week ends -- the partial SOC week itself never owes a visit.
    """
    soc_week_end = _week_end_saturday(soc_date)
    return soc_week_end + timedelta(days=1)


def _get_current_admission(db: Session, *, tenant_id: UUID, patient_id: UUID) -> Optional[Admission]:
    return (
        db.query(Admission)
        .filter(
            Admission.tenant_id == tenant_id,
            Admission.patient_id == patient_id,
            Admission.soc_date.isnot(None),
        )
        .order_by(Admission.discharged_at.is_(None).desc(), Admission.admission_date.desc())
        .first()
    )


def _has_active_assignment(db: Session, *, tenant_id: UUID, patient_id: UUID, discipline: str) -> bool:
    return (
        db.query(PatientAssignment.id)
        .filter(
            PatientAssignment.tenant_id == tenant_id,
            PatientAssignment.patient_id == patient_id,
            PatientAssignment.discipline == discipline,
            PatientAssignment.active.is_(True),
        )
        .first()
        is not None
    )


def _qualifying_rn_supervisory_visit(
    db: Session,
    *,
    tenant_id: UUID,
    patient_id: UUID,
    cycle_start: date,
    cycle_end: date,
):
    """
    Find the earliest qualifying RN supervisory visit within [cycle_start, cycle_end].
    Qualifying = RN visit_type, is_supervisory flag OR SUPV_VISIT_ONLY form_type,
    not deleted, not MISSED/CANCELLED/DRAFT, and not a PRN/SHORT_FORM visit.
    """
    start_dt = datetime.combine(cycle_start, datetime.min.time())
    end_dt = datetime.combine(cycle_end, datetime.max.time())
    return (
        db.query(Visit)
        .filter(
            Visit.tenant_id == tenant_id,
            Visit.patient_id == patient_id,
            Visit.deleted_at.is_(None),
            Visit.visit_type == "RN",
            Visit.form_type != "SHORT_FORM",
            Visit.visit_datetime >= start_dt,
            Visit.visit_datetime <= end_dt,
            ~Visit.status.in_(_NON_QUALIFYING_STATUSES),
            (Visit.is_supervisory.is_(True)) | (Visit.form_type == "SUPV_VISIT_ONLY"),
        )
        .order_by(Visit.visit_datetime.asc())
        .first()
    )


def _build_cycles(effective_start: date, today: date, cadence_days: int) -> list[tuple[date, date]]:
    """
    Build every closed/open cadence cycle from effective_start through the
    cycle currently in progress (inclusive), plus exactly one upcoming cycle.
    """
    cycles: list[tuple[date, date]] = []
    if today < effective_start:
        # First cycle hasn't started yet -- return just the upcoming one.
        cycles.append((effective_start, effective_start + timedelta(days=cadence_days - 1)))
        return cycles

    cycle_start = effective_start
    while cycle_start <= today:
        cycle_end = cycle_start + timedelta(days=cadence_days - 1)
        cycles.append((cycle_start, cycle_end))
        cycle_start = cycle_end + timedelta(days=1)
    # One upcoming cycle beyond "today" so the UI can show what's next.
    cycles.append((cycle_start, cycle_start + timedelta(days=cadence_days - 1)))
    return cycles


def _summarize_discipline(
    db: Session,
    *,
    tenant_id: UUID,
    patient_id: UUID,
    effective_start: date,
    today: date,
    cadence_days: int,
) -> dict:
    cycles = _build_cycles(effective_start, today, cadence_days)
    overdue_cycle = None
    current_cycle = None
    upcoming_cycle = cycles[-1]
    last_satisfying_visit = None

    for cycle_start, cycle_end in cycles[:-1]:  # exclude the trailing upcoming cycle
        visit = _qualifying_rn_supervisory_visit(
            db, tenant_id=tenant_id, patient_id=patient_id, cycle_start=cycle_start, cycle_end=cycle_end
        )
        if visit is not None:
            last_satisfying_visit = visit
            continue
        if cycle_end < today:
            if overdue_cycle is None:
                overdue_cycle = (cycle_start, cycle_end)
        else:
            current_cycle = (cycle_start, cycle_end)

    if overdue_cycle:
        status = "OVERDUE"
        due_date = overdue_cycle[1]
    elif current_cycle:
        status = "DUE"
        due_date = current_cycle[1]
    elif today < effective_start:
        status = "NOT_YET_DUE"
        due_date = upcoming_cycle[1]
    else:
        status = "SATISFIED"
        due_date = upcoming_cycle[1]

    return {
        "required": True,
        "cadence_days": cadence_days,
        "status": status,
        "due_date": due_date.isoformat(),
        "last_satisfying_visit_id": str(last_satisfying_visit.id) if last_satisfying_visit else None,
        "last_satisfying_visit_date": (
            last_satisfying_visit.visit_datetime.date().isoformat() if last_satisfying_visit else None
        ),
    }


def compute_supervisory_schedule(db: Session, *, tenant_id: UUID, patient_id: UUID) -> dict:
    """
    Public entry point. Returns a dict with "chha_supervisory" and
    "lvn_supervisory" keys, each either {"required": False, "reason": "..."}
    or a full status dict from _summarize_discipline.
    """
    admission = _get_current_admission(db, tenant_id=tenant_id, patient_id=patient_id)
    if admission is None or admission.soc_date is None:
        no_soc = {"required": False, "reason": "No Start of Care date on file"}
        return {"chha_supervisory": no_soc, "lvn_supervisory": no_soc, "soc_date": None}

    soc_date = (
        admission.soc_date.date() if isinstance(admission.soc_date, datetime) else admission.soc_date
    )
    has_chha = _has_active_assignment(db, tenant_id=tenant_id, patient_id=patient_id, discipline="CHHA")
    has_lvn = _has_active_assignment(db, tenant_id=tenant_id, patient_id=patient_id, discipline="LVN")
    if not has_lvn:
        has_lvn = _has_active_assignment(db, tenant_id=tenant_id, patient_id=patient_id, discipline="LPN")

    today = datetime.now(timezone.utc).date()
    effective_start = _effective_cadence_start(soc_date)

    if not has_chha and not has_lvn:
        # RN-only care: no supervisory documentation required at all.
        none_required = {"required": False, "reason": "No active CHHA or LVN assignment — RN-only care"}
        return {"chha_supervisory": none_required, "lvn_supervisory": none_required, "soc_date": soc_date.isoformat()}

    chha_result = (
        _summarize_discipline(
            db,
            tenant_id=tenant_id,
            patient_id=patient_id,
            effective_start=effective_start,
            today=today,
            cadence_days=CHHA_CADENCE_DAYS,
        )
        if has_chha
        else {"required": False, "reason": "No active CHHA assignment"}
    )
    lvn_result = (
        _summarize_discipline(
            db,
            tenant_id=tenant_id,
            patient_id=patient_id,
            effective_start=effective_start,
            today=today,
            cadence_days=LVN_CADENCE_DAYS,
        )
        if has_lvn
        else {"required": False, "reason": "No active LVN/LPN assignment"}
    )

    return {
        "chha_supervisory": chha_result,
        "lvn_supervisory": lvn_result,
        "soc_date": soc_date.isoformat(),
        "effective_cadence_start": effective_start.isoformat(),
    }

