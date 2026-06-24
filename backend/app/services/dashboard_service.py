from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.clinical_note import ClinicalNote
from app.models.incident_report import IncidentReport
from app.models.task import Task
from app.services.idg_engine import enforce_idg_readiness


# =========================================================
# RESPONSE DTOs
# =========================================================

@dataclass
class DashboardMetric:
    key: str
    label: str
    value: int


@dataclass
class DashboardPatientBlocker:
    patient_id: str
    blockers: list[str]


@dataclass
class DashboardTaskItem:
    task_id: str
    patient_id: str
    task_type: str
    status: str
    due_date: str | None
    due_at: str | None
    clinical_note_id: str | None
    incident_id: str | None


@dataclass
class DashboardIncidentItem:
    incident_id: str
    patient_id: str
    incident_type: str
    incident_severity: str
    incident_date: str | None
    clinical_note_id: str | None


@dataclass
class DashboardNoteFlagItem:
    note_id: str
    patient_id: str
    encounter_date: str | None
    discipline: str | None
    visit_type: str | None
    note_category: str | None
    incident_required: bool
    incident_status: str | None
    red_flags: list[str]
    needs_clarification: list[str]


@dataclass
class DashboardResponse:
    metrics: list[dict[str, Any]]
    task_type_counts: dict[str, int]
    incident_type_counts: dict[str, int]
    open_tasks: list[dict[str, Any]]
    pending_incidents: list[dict[str, Any]]
    flagged_notes: list[dict[str, Any]]
    blocked_patients: list[dict[str, Any]]


# =========================================================
# PUBLIC ENTRYPOINTS
# =========================================================

def get_clinical_compliance_dashboard(
    db: Session,
    *,
    tenant_id: UUID,
) -> dict[str, Any]:
    tasks = _load_tenant_tasks(db, tenant_id)
    notes = _load_tenant_notes(db, tenant_id)
    incidents = _load_tenant_incidents(db, tenant_id)

    open_tasks = [task for task in tasks if _task_is_open(task)]
    pending_incidents = [
        incident for incident in incidents if not getattr(incident, "signed_at", None)
    ]
    flagged_notes = [note for note in notes if _has_flagged_content(note)]

    patient_ids = sorted(
        {
            str(getattr(note, "patient_id"))
            for note in notes
            if getattr(note, "patient_id", None) is not None
        }
    )

    blocked_patients: list[DashboardPatientBlocker] = []
    for patient_id in patient_ids:
        check = enforce_idg_readiness(
            db=db,
            patient_id=UUID(patient_id),
            tenant_id=tenant_id,
        )
        if check.blocked:
            blocked_patients.append(
                DashboardPatientBlocker(
                    patient_id=patient_id,
                    blockers=check.reasons,
                )
            )

    metrics = [
        DashboardMetric(key="open_tasks", label="Open Tasks", value=len(open_tasks)),
        DashboardMetric(
            key="pending_incidents",
            label="Pending Incidents",
            value=len(pending_incidents),
        ),
        DashboardMetric(
            key="flagged_notes",
            label="Flagged Notes",
            value=len(flagged_notes),
        ),
        DashboardMetric(
            key="idg_blocked_patients",
            label="IDG Blocked Patients",
            value=len(blocked_patients),
        ),
    ]

    task_type_counts = Counter(
        _enumish(getattr(task, "task_type", None)) for task in open_tasks
    )
    incident_type_counts = Counter(
        _enumish(getattr(incident, "incident_type", None))
        for incident in pending_incidents
    )

    response = DashboardResponse(
        metrics=[asdict(metric) for metric in metrics],
        task_type_counts={
            key: value for key, value in sorted(task_type_counts.items()) if key
        },
        incident_type_counts={
            key: value for key, value in sorted(incident_type_counts.items()) if key
        },
        open_tasks=[asdict(_map_task(task)) for task in open_tasks],
        pending_incidents=[
            asdict(_map_incident(incident)) for incident in pending_incidents
        ],
        flagged_notes=[asdict(_map_note(note)) for note in flagged_notes],
        blocked_patients=[asdict(item) for item in blocked_patients],
    )

    return asdict(response)


def get_patient_compliance_detail(
    db: Session,
    *,
    tenant_id: UUID,
    patient_id: UUID,
) -> dict[str, Any]:
    tasks = [
        task
        for task in _load_tenant_tasks(db, tenant_id)
        if str(getattr(task, "patient_id", "")) == str(patient_id)
    ]
    notes = [
        note
        for note in _load_tenant_notes(db, tenant_id)
        if str(getattr(note, "patient_id", "")) == str(patient_id)
    ]
    incidents = [
        incident
        for incident in _load_tenant_incidents(db, tenant_id)
        if str(getattr(incident, "patient_id", "")) == str(patient_id)
    ]

    idg = enforce_idg_readiness(
        db=db,
        patient_id=patient_id,
        tenant_id=tenant_id,
    )

    return {
        "patient_id": str(patient_id),
        "blocked": idg.blocked,
        "blockers": idg.reasons,
        "tasks": [asdict(_map_task(task)) for task in tasks],
        "incidents": [asdict(_map_incident(incident)) for incident in incidents],
        "notes": [asdict(_map_note(note)) for note in notes],
    }


def get_owner_dashboard(
    db: Session,
) -> dict[str, Any]:
    """
    System-wide owner dashboard.

    Safe for staged rollout even if payments / claim_status are not ready yet.
    """

    total_tenants = _safe_scalar(db, text("SELECT COUNT(*) FROM tenants")) or 0
    total_tasks = _safe_scalar(db, text("SELECT COUNT(*) FROM tasks")) or 0
    total_incidents = _safe_scalar(db, text("SELECT COUNT(*) FROM incident_reports")) or 0
    total_notes = _safe_scalar(db, text("SELECT COUNT(*) FROM clinical_notes")) or 0

    total_payments = _safe_scalar(db, text("SELECT COUNT(*) FROM payments")) or 0
    total_denials = (
        _safe_scalar(
            db,
            text(
                """
                SELECT COUNT(*)
                FROM payments
                WHERE is_denied = TRUE
                """
            ),
        )
        or 0
    )

    tenant_rows = (
        db.execute(
            text(
                """
                SELECT
                    t.id::text AS tenant_id,
                    COALESCE(t.display_name, t.legal_name, t.id::text) AS tenant_name
                FROM tenants t
                ORDER BY tenant_name
                """
            )
        )
        .mappings()
        .all()
    )

    tenant_summary: list[dict[str, Any]] = []

    for row in tenant_rows:
        tenant_id = row["tenant_id"]

        open_tasks = (
            _safe_scalar(
                db,
                text(
                    """
                    SELECT COUNT(*)
                    FROM tasks
                    WHERE tenant_id = :tenant_id
                      AND status IN ('PENDING', 'PENDING', 'OVERDUE')
                    """
                ),
                {"tenant_id": tenant_id},
            )
            or 0
        )

        incidents = (
            _safe_scalar(
                db,
                text(
                    """
                    SELECT COUNT(*)
                    FROM incident_reports
                    WHERE tenant_id = :tenant_id
                    """
                ),
                {"tenant_id": tenant_id},
            )
            or 0
        )

        blocked_patients = 0

        tenant_summary.append(
            {
                "tenant_id": tenant_id,
                "tenant_name": row["tenant_name"],
                "open_tasks": open_tasks,
                "incidents": incidents,
                "blocked_patients": blocked_patients,
            }
        )

    recent_incidents = (
        db.query(IncidentReport)
        .order_by(getattr(IncidentReport, "created_at").desc())
        .limit(10)
        .all()
    )

    return {
        "metrics": [
            {"key": "tenants", "label": "Total Tenants", "value": total_tenants},
            {"key": "tasks", "label": "Active Tasks", "value": total_tasks},
            {"key": "incidents", "label": "System Incidents", "value": total_incidents},
            {"key": "notes", "label": "Clinical Notes", "value": total_notes},
            {"key": "payments", "label": "Payments Posted", "value": total_payments},
            {"key": "denials", "label": "Denied Claims", "value": total_denials},
        ],
        "total_tenants": total_tenants,
        "active_tasks": total_tasks,
        "system_incidents": total_incidents,
        "clinical_notes": total_notes,
        "payments_posted": total_payments,
        "denied_claims": total_denials,
        "tenant_summary": tenant_summary,
        "recent_incidents": [asdict(_map_incident(item)) for item in recent_incidents],
    }


def get_billing_dashboard(
    db: Session,
    *,
    tenant_id: UUID,
) -> dict[str, Any]:
    """
    Billing dashboard with 835-aware metrics.

    Safe for staged rollout:
    - If `payments` table does not exist yet → returns 0 metrics
    - If `claim_status` table does not exist yet → returns 0 pending payment count
    """

    payments_received = (
        _safe_scalar(
            db,
            text(
                """
                SELECT COUNT(*)
                FROM payments
                WHERE tenant_id = :tenant_id
                  AND COALESCE(total_paid, 0) > 0
                """
            ),
            {"tenant_id": str(tenant_id)},
        )
        or 0
    )

    denied_claims = (
        _safe_scalar(
            db,
            text(
                """
                SELECT COUNT(*)
                FROM payments
                WHERE tenant_id = :tenant_id
                  AND is_denied = TRUE
                """
            ),
            {"tenant_id": str(tenant_id)},
        )
        or 0
    )

    claims_pending_payment = (
        _safe_scalar(
            db,
            text(
                """
                SELECT COUNT(*)
                FROM claim_status
                WHERE tenant_id = :tenant_id
                  AND status IN ('SENT', 'ACCEPTED')
                """
            ),
            {"tenant_id": str(tenant_id)},
        )
        or 0
    )

    remittance_files_processed = (
        _safe_scalar(
            db,
            text(
                """
                SELECT COUNT(*)
                FROM payments
                WHERE tenant_id = :tenant_id
                """
            ),
            {"tenant_id": str(tenant_id)},
        )
        or 0
    )

    billing_holds: list[dict[str, Any]] = []

    return {
        "metrics": [
            {
                "key": "payments_received",
                "label": "Payments Received",
                "value": payments_received,
            },
            {
                "key": "denied_claims",
                "label": "Denied Claims",
                "value": denied_claims,
            },
            {
                "key": "claims_pending_payment",
                "label": "Pending Payment",
                "value": claims_pending_payment,
            },
            {
                "key": "remittance_files_processed",
                "label": "835 Records Posted",
                "value": remittance_files_processed,
            },
        ],
        "payments_received": payments_received,
        "denied_claims": denied_claims,
        "claims_pending_payment": claims_pending_payment,
        "remittance_files_processed": remittance_files_processed,
        "billing_holds": billing_holds,
    }


# =========================================================
# LOADERS
# =========================================================

def _load_tenant_tasks(db: Session, tenant_id: UUID) -> list[Task]:
    return (
        db.query(Task)
        .filter(Task.tenant_id == tenant_id)
        .order_by(getattr(Task, "created_at").desc())
        .all()
    )


def _load_tenant_notes(db: Session, tenant_id: UUID) -> list[ClinicalNote]:
    return (
        db.query(ClinicalNote)
        .filter(ClinicalNote.tenant_id == tenant_id)
        .order_by(getattr(ClinicalNote, "created_at").desc())
        .all()
    )


def _load_tenant_incidents(db: Session, tenant_id: UUID) -> list[IncidentReport]:
    return (
        db.query(IncidentReport)
        .filter(IncidentReport.tenant_id == tenant_id)
        .order_by(getattr(IncidentReport, "created_at").desc())
        .all()
    )


# =========================================================
# MAPPERS
# =========================================================

def _map_task(task: Task) -> DashboardTaskItem:
    return DashboardTaskItem(
        task_id=str(getattr(task, "id")),
        patient_id=str(getattr(task, "patient_id")),
        task_type=_enumish(getattr(task, "task_type", None)),
        status=_enumish(getattr(task, "status", None)),
        due_date=_iso(getattr(task, "due_date", None)),
        due_at=_iso(getattr(task, "due_at", None)),
        clinical_note_id=_uuidish(getattr(task, "clinical_note_id", None)),
        incident_id=_uuidish(getattr(task, "incident_id", None)),
    )


def _map_incident(incident: IncidentReport) -> DashboardIncidentItem:
    return DashboardIncidentItem(
        incident_id=str(getattr(incident, "id")),
        patient_id=str(getattr(incident, "patient_id")),
        incident_type=_enumish(getattr(incident, "incident_type", None)),
        incident_severity=_enumish(getattr(incident, "incident_severity", None)),
        incident_date=_iso(getattr(incident, "incident_date", None)),
        clinical_note_id=_uuidish(getattr(incident, "clinical_note_id", None)),
    )


def _map_note(note: ClinicalNote) -> DashboardNoteFlagItem:
    return DashboardNoteFlagItem(
        note_id=str(getattr(note, "id")),
        patient_id=str(getattr(note, "patient_id")),
        encounter_date=_iso(getattr(note, "encounter_date", None)),
        discipline=_enumish(getattr(note, "discipline", None)),
        visit_type=_enumish(getattr(note, "visit_type", None)),
        note_category=_enumish(getattr(note, "note_category", None)),
        incident_required=_truthy(getattr(note, "incident_required", False)),
        incident_status=_enumish(getattr(note, "incident_status", None)),
        red_flags=_listish(getattr(note, "red_flags", None)),
        needs_clarification=_listish(getattr(note, "needs_clarification", None)),
    )


# =========================================================
# HELPERS
# =========================================================

def _safe_scalar(
    db: Session,
    statement,
    params: dict[str, Any] | None = None,
) -> Any:
    try:
        result = db.execute(statement, params or {})
        return result.scalar()
    except SQLAlchemyError:
        return 0


def _task_is_open(task: Task) -> bool:
    status = _enumish(getattr(task, "status", None)).upper()
    return status in {"PENDING", "PENDING", "OVERDUE"}


def _has_flagged_content(note: ClinicalNote) -> bool:
    return (
        len(_listish(getattr(note, "red_flags", None))) > 0
        or len(_listish(getattr(note, "needs_clarification", None))) > 0
        or _truthy(getattr(note, "incident_required", False))
    )


def _listish(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(v) for v in value]
    return []


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def _enumish(value: Any) -> str:
    if value is None:
        return ""
    if hasattr(value, "value"):
        return str(value.value)
    return str(value)


def _uuidish(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _iso(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)

def get_claim_lifecycle_dashboard(
    db: Session,
    *,
    tenant_id: UUID,
) -> dict[str, Any]:
    """
    Claim lifecycle distribution.

    SAFE:
    - returns 0 if table missing
    - no crash during rollout
    """

    def _count(status: str) -> int:
        return (
            _safe_scalar(
                db,
                text(
                    """
                    SELECT COUNT(*)
                    FROM claim_status
                    WHERE tenant_id = :tenant_id
                      AND status = :status
                    """
                ),
                {"tenant_id": str(tenant_id), "status": status},
            )
            or 0
        )

    ready = _count("READY")
    sent = _count("SENT")
    accepted = _count("ACCEPTED")
    paid = _count("PAID")
    denied = _count("DENIED")

    return {
        "metrics": [
            {"key": "ready", "label": "Ready", "value": ready},
            {"key": "sent", "label": "Sent", "value": sent},
            {"key": "accepted", "label": "Accepted", "value": accepted},
            {"key": "paid", "label": "Paid", "value": paid},
            {"key": "denied", "label": "Denied", "value": denied},
        ],
        "ready": ready,
        "sent": sent,
        "accepted": accepted,
        "paid": paid,
        "denied": denied,
    }
