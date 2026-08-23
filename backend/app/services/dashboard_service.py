from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.clinical_note import ClinicalNote
from app.models.certification import Certification
from app.models.incident_report import IncidentReport
from app.models.patient import Patient
from app.models.patient_assignment import PatientAssignment
from app.models.patient_facesheet import PatientFaceSheet
from app.models.physician_order import PhysicianOrder
from app.models.rnica_assessment import RnicaAssessment
from app.models.task import Task
from app.models.admission import Admission
from app.models.plan_of_care import PlanOfCare
from app.models.user import User
from app.models.enums import TaskStatus
from app.services.idg_engine import enforce_idg_readiness
from app.services.clinical_note_validation_engine import get_note_validation_flags
from app.services.certification_service import CTI_SIGNER_ROLES
from app.services import physician_identity_service
from app.core.names import person_name_expression
from app.core.roles import normalize_role


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
class DashboardClinicalAlertItem:
    alert_id: str
    priority: str
    alert_type: str
    patient_id: str
    patient_name: str
    description: str
    generated: str | None
    status: str
    source_type: str


@dataclass
class DashboardOrderItem:
    order_id: str
    patient_id: str
    patient_name: str
    order_category: str
    order_text: str
    status: str
    source_type: str
    ordered_by_provider_name: str
    ordered_by_provider_role: str
    entered_by_name: str | None
    ordered_at: str | None
    signed_by_name: str | None
    signed_at: str | None


@dataclass
class DashboardResponse:
    metrics: list[dict[str, Any]]
    task_type_counts: dict[str, int]
    incident_type_counts: dict[str, int]
    open_tasks: list[dict[str, Any]]
    pending_incidents: list[dict[str, Any]]
    flagged_notes: list[dict[str, Any]]
    blocked_patients: list[dict[str, Any]]
    unsigned_orders: list[dict[str, Any]]
    all_orders: list[dict[str, Any]]
    compliance_queue: dict[str, Any]


# =========================================================
# PUBLIC ENTRYPOINTS
# =========================================================

def get_clinical_compliance_dashboard(
    db: Session,
    *,
    tenant_id: UUID,
    role: str | None = None,
    user_id: UUID | None = None,
) -> dict[str, Any]:
    tasks = _load_tenant_tasks(db, tenant_id)
    notes = _load_tenant_notes(db, tenant_id)
    incidents = _load_tenant_incidents(db, tenant_id)
    unsigned_orders = _load_unsigned_orders(db, tenant_id)
    clinical_review_orders = _load_orders_pending_clinical_review(db, tenant_id)
    all_orders = _load_all_orders(db, tenant_id)

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
        DashboardMetric(
            key="unsigned_orders",
            label="Orders Awaiting MD Signature",
            value=len(unsigned_orders),
        ),
    ]

    task_type_counts = Counter(
        _enumish(getattr(task, "task_type", None)) for task in open_tasks
    )
    incident_type_counts = Counter(
        _enumish(getattr(incident, "incident_type", None))
        for incident in pending_incidents
    )

    compliance_queue = _build_compliance_queue(
        db,
        tenant_id=tenant_id,
        open_tasks=open_tasks,
        unsigned_orders=unsigned_orders,
        clinical_review_orders=clinical_review_orders,
        blocked_patients=blocked_patients,
        role=role,
        user_id=user_id,
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
        unsigned_orders=[asdict(item) for item in unsigned_orders],
        all_orders=[asdict(item) for item in all_orders],
        compliance_queue=compliance_queue,
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


def get_clinical_alerts_dashboard(
    db: Session,
    *,
    tenant_id: UUID,
) -> dict[str, Any]:
    alert_rows: list[DashboardClinicalAlertItem] = []

    patient_name_col = person_name_expression(PatientFaceSheet, Patient.mrn).label("patient_name")

    task_rows = (
        db.query(Task, patient_name_col)
        .join(Patient, Patient.id == Task.patient_id)
        .outerjoin(PatientFaceSheet, PatientFaceSheet.patient_id == Patient.id)
        .filter(Task.tenant_id == tenant_id)
        .filter(Task.status.in_([TaskStatus.PENDING, TaskStatus.OVERDUE, TaskStatus.ESCALATED]))
        .order_by(Task.created_at.desc())
        .all()
    )

    for task, patient_name in task_rows:
        severity = _task_alert_priority(task)
        alert_rows.append(
            DashboardClinicalAlertItem(
                alert_id=f"task:{task.id}",
                priority=severity,
                alert_type=_task_alert_title(task),
                patient_id=str(task.patient_id),
                patient_name=patient_name,
                description=_task_alert_description(task),
                generated=_iso(getattr(task, "created_at", None) or getattr(task, "due_at", None)),
                status="Open" if _enumish(getattr(task, "status", None)).upper() != "COMPLETED" else "Acknowledged",
                source_type="TASK",
            )
        )

    incident_rows = (
        db.query(IncidentReport, patient_name_col)
        .join(Patient, Patient.id == IncidentReport.patient_id)
        .outerjoin(PatientFaceSheet, PatientFaceSheet.patient_id == Patient.id)
        .filter(IncidentReport.tenant_id == tenant_id)
        .filter(IncidentReport.signed_at.is_(None))
        .order_by(IncidentReport.created_at.desc(), IncidentReport.incident_date.desc())
        .all()
    )

    for incident, patient_name in incident_rows:
        alert_rows.append(
            DashboardClinicalAlertItem(
                alert_id=f"incident:{incident.id}",
                priority=_incident_alert_priority(incident),
                alert_type=_enumish(getattr(incident, "incident_type", None)) or "Incident",
                patient_id=str(incident.patient_id),
                patient_name=patient_name,
                description=_incident_alert_description(incident),
                generated=_iso(getattr(incident, "created_at", None) or getattr(incident, "incident_date", None)),
                status="Open",
                source_type="INCIDENT",
            )
        )

    # Validation flags (red_flags / needs_clarification / incident_required) are
    # persisted inside ClinicalNote.content["_validation"], not as top-level
    # columns, so filtering has to happen in Python via get_note_validation_flags
    # after loading candidate notes (see get_note_validation_flags docstring).
    candidate_notes = (
        db.query(ClinicalNote, patient_name_col)
        .join(Patient, Patient.id == ClinicalNote.patient_id)
        .outerjoin(PatientFaceSheet, PatientFaceSheet.patient_id == Patient.id)
        .filter(ClinicalNote.tenant_id == tenant_id)
        .order_by(ClinicalNote.created_at.desc())
        .all()
    )
    note_rows = [
        (note, patient_name)
        for note, patient_name in candidate_notes
        if _has_flagged_content(note)
    ]

    for note, patient_name in note_rows:
        alert_rows.append(
            DashboardClinicalAlertItem(
                alert_id=f"note:{note.id}",
                priority=_note_alert_priority(note),
                alert_type=_enumish(getattr(note, "form_key", None)) or _enumish(getattr(note, "note_type", None)) or "Clinical Note",
                patient_id=str(note.patient_id),
                patient_name=patient_name,
                description=_note_alert_description(note),
                generated=_iso(getattr(note, "created_at", None) or getattr(note, "encounter_date", None)),
                status="Open" if get_note_validation_flags(note).get("incident_required") else "Acknowledged",
                source_type="NOTE",
            )
        )

    if not alert_rows:
        patient_row = (
            db.query(Patient, patient_name_col)
            .outerjoin(PatientFaceSheet, PatientFaceSheet.patient_id == Patient.id)
            .filter(Patient.tenant_id == tenant_id)
            .order_by(Patient.created_at.desc())
            .first()
        )

        if patient_row is not None:
            patient, full_name = patient_row
            assessment = (
                db.query(RnicaAssessment)
                .filter(RnicaAssessment.patient_id == patient.id)
                .order_by(RnicaAssessment.created_at.desc())
                .first()
            )

            if assessment is not None:
                election_signed = getattr(patient, "election_signed_at", None) is not None
                admission_status = _enumish(getattr(patient, "admission_status", None)) or "Unknown"
                locked = _truthy(getattr(assessment, "locked", False))

                if not election_signed:
                    alert_rows.append(
                        DashboardClinicalAlertItem(
                            alert_id=f"patient:{patient.id}:election",
                            priority="High",
                            alert_type="Election Packet Review",
                            patient_id=str(patient.id),
                            patient_name=full_name,
                            description=(
                                f"{full_name} has no signed election packet on file and needs review."
                            ),
                            generated=_iso(getattr(patient, "updated_at", None) or getattr(patient, "created_at", None)),
                            status="Open",
                            source_type="PATIENT",
                        )
                    )

                if admission_status in {"PRE_REFERRAL", "PENDING"}:
                    alert_rows.append(
                        DashboardClinicalAlertItem(
                            alert_id=f"patient:{patient.id}:admission",
                            priority="Critical" if admission_status == "PRE_REFERRAL" else "High",
                            alert_type="Admission Status Review",
                            patient_id=str(patient.id),
                            patient_name=full_name,
                            description=(
                                f"{full_name} is still marked {admission_status.lower().replace('_', ' ')} "
                                "and needs admission follow-up."
                            ),
                            generated=_iso(getattr(patient, "updated_at", None) or getattr(patient, "created_at", None)),
                            status="Open",
                            source_type="PATIENT",
                        )
                    )

                if locked:
                    alert_rows.append(
                        DashboardClinicalAlertItem(
                            alert_id=f"assessment:{assessment.id}",
                            priority="Medium",
                            alert_type="RNICA Finalized",
                            patient_id=str(patient.id),
                            patient_name=full_name,
                            description=(
                                f"RNICA assessment for {full_name} is locked and care plan finalization is recorded."
                            ),
                            generated=_iso(getattr(assessment, "locked_at", None) or getattr(assessment, "created_at", None)),
                            status="Acknowledged",
                            source_type="ASSESSMENT",
                        )
                    )

    alert_rows.sort(
        key=lambda item: (
            _priority_rank(item.priority),
            item.generated or "",
        ),
        reverse=True,
    )

    open_count = sum(1 for item in alert_rows if item.status == "Open")
    critical_count = sum(1 for item in alert_rows if item.priority == "Critical")
    resolved_count = sum(1 for item in alert_rows if item.status != "Open")

    return {
        "metrics": [
            {"key": "open_alerts", "label": "Total Open Alerts", "value": open_count},
            {"key": "critical_alerts", "label": "Critical Priority", "value": critical_count},
            {"key": "resolved_alerts", "label": "Resolved Today", "value": resolved_count},
        ],
        "alerts": [asdict(item) for item in alert_rows[:100]],
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

# =========================================================
# COMPLIANCE ACTION QUEUE (real data only — no placeholder counts)
# =========================================================

CTI_TASK_TYPES = {"CERTIFICATION", "RECERTIFICATION"}
CARE_PLAN_TASK_TYPES = {
    "POC_REVIEW_REQUIRED",
    "POC_STALE_REVIEW",
    "POC_NONCOMPLIANT_STRUCTURE",
    "POC_PHYSICIAN_REVIEW_REQUIRED",
}
ADMISSION_PIPELINE_STATUSES = [
    "REFERRAL",
    "POTENTIAL_ADMISSION",
    "ADMISSION_SCHEDULED",
    "TRANSFER_PENDING",
    "SOC_IN_PROGRESS",
]

# ---------------------------------------------------------------
# WIDGET VISIBILITY ENGINE
#
# The dashboard is not one universal view — each widget declares which
# canonical roles (see app.core.roles) may see it, and field-clinician
# roles are additionally scoped down to only their own assigned patients
# rather than the whole tenant.
#
# Authority separation: seeing a problem, coordinating it, correcting it,
# signing it, and monitoring agency-wide compliance are distinct
# authorities and are modeled as distinct widget keys rather than one
# widget with multiple audiences. The same underlying unsigned-order queue
# is surfaced as THREE separate widget keys, each with its own action:
#   - md_signatures_pending_oversight: Administrator/DPCS/DPCS_ADMINISTRATOR/
#     Clinical Supervisor/Compliance/QA may VIEW or MONITOR the backlog for
#     agency oversight and survey-readiness purposes. This is a read-only
#     queue — action label "Review Queue" — and must NEVER be labeled as
#     signature authority. Backend enforcement lives independently at
#     POST /physician-orders/{id}/approve and POST /idg/.../batch-sign,
#     both of which require an actual prescriber role via
#     require_roles(..., allow_clinical_admin=False) — dashboard visibility
#     of this widget grants no signing capability whatsoever.
#   - orders_requiring_provider_signature (renamed from
#     orders_requiring_my_signature) — the actual credentialed signer's queue
#     (Medical Director / Attending Physician / Hospice Physician / Medical
#     Director Designee, plus alternate authorized provider signers NP/PA
#     for STAT/URGENT eligible-category orders — see Provider Signature
#     Authority Model in app/services/physician_order_service.py) — action
#     label "Review and Sign". Per-patient scoping is now enforced via
#     Physician Identity Mapping (see SIGNATURE_SCOPING_NOT_YET_IMPLEMENTED
#     note below): an unverified provider-identity account sees zero orders;
#     a verified Medical Director/Designee (or legacy "MD") sees tenant-wide;
#     a verified Attending Physician/Hospice Physician/NP/PA sees only orders
#     for their own PatientAssignment-scoped patients.
#   - orders_requiring_clinical_follow_up (renamed from
#     orders_requiring_clinical_action): the RN/LVN/DPCS/Clinical
#     Supervisor's coordination duty for the same underlying orders — they
#     can follow up and prep the order, but they cannot discharge the
#     physician's signature obligation. Action label "Open Follow-up".
# ---------------------------------------------------------------

# Physician Identity Mapping (owner directive 2026-08-21) closed the gap
# this flag used to document: orders_requiring_provider_signature (and the
# rest of _build_compliance_queue's provider-role-scoped widgets) are now
# scoped via physician_identity_service.authorized_patient_ids_for_provider()
# — fail-closed for an unverified provider-identity account, tenant-wide for
# a verified Medical Director/Designee, assigned-patient-only for a verified
# Attending Physician/Hospice Physician/NP/PA. Kept as False (rather than
# deleting the flag/name) so any code or docs still checking it fail loudly
# instead of silently assuming the old agency-wide behavior.
#
# Residual gap (not yet covered by this pass): CTI and F2F have their own
# separate signer/performer models (certification_service.py, f2f_service.py)
# that are not yet integrated with this same physician_id linkage for
# patient-level dashboard scoping — CTI/F2F dashboard widgets remain
# agency-wide for their respective roles until that follow-up work lands.
SIGNATURE_SCOPING_NOT_YET_IMPLEMENTED = False

# "Compliance" oversight roles (QA_ROLES from app.core.roles): read-only
# agency-wide monitoring, per CMS/CDPH survey-readiness and documentation
# accountability. They see the SAME agency-wide monitoring widgets as
# ADMINISTRATOR/DPCS, but never actual signature authority
# (orders_requiring_provider_signature) and never RN/LVN care-coordination duty
# (orders_requiring_clinical_follow_up) — they may still MONITOR the
# signature backlog (md_signatures_pending_oversight) alongside ADMINISTRATOR/
# DPCS/Clinical Supervisor, but never Intake's admissions pipeline —
# monitoring is a distinct
# authority from signing, coordinating, or admitting.
COMPLIANCE_OVERSIGHT_ROLES = {"COMPLIANCE_OFFICER", "QA_MANAGER", "QA_REVIEWER"}

# Roles that hold agency-wide (not caseload-scoped) compliance-monitoring
# authority: ADMINISTRATOR/DPCS/DPCS_ADMINISTRATOR plus the QA/Compliance
# oversight roles above.
_AGENCY_COMPLIANCE_ROLES = {"ADMINISTRATOR", "DPCS", "DPCS_ADMINISTRATOR"} | COMPLIANCE_OVERSIGHT_ROLES

WIDGET_VISIBILITY: dict[str, set[str]] = {
    # View/monitor only — never implies signing capability. See the
    # authority-separation note above and require_roles(allow_clinical_admin=False)
    # on the real signing endpoints.
    "md_signatures_pending_oversight": (
        {"ADMINISTRATOR", "DPCS", "DPCS_ADMINISTRATOR", "CLINICAL_SUPERVISOR"}
        | COMPLIANCE_OVERSIGHT_ROLES
    ),
    # The actual credentialed signer's queue. Deliberately excludes
    # Administrator/DPCS/Clinical Supervisor/Compliance/QA — administrative
    # rank and oversight are never signature authority. Includes both
    # primary providers (Attending Physician/Hospice Physician/Medical
    # Director/Medical Director Designee) and alternate authorized
    # provider signers (NP/PA) — the STAT/URGENT eligible-category
    # restriction on NP/PA is enforced at the API/service layer
    # (svc.is_authorized_order_signer), not dashboard visibility, matching
    # the CTI/F2F precedent that dashboard visibility != actual authorization.
    "orders_requiring_provider_signature": {
        "MEDICAL_DIRECTOR", "ATTENDING_PHYSICIAN", "HOSPICE_PHYSICIAN", "NP", "PA",
    },
    # Clinical coordination duty on the same orders — not a signature action.
    "orders_requiring_clinical_follow_up": {"RN", "LVN", "CLINICAL_SUPERVISOR", "DPCS", "DPCS_ADMINISTRATOR"},
    # Phase 1 lifecycle expansion (2026-08-21): orders conditionally routed
    # to PENDING_CLINICAL_REVIEW (non-clinical/office-entered, incomplete
    # authentication, or returned-for-clarification orders) — a distinct
    # queue from clinical follow-up on already-signed orders.
    "orders_pending_clinical_review": {"RN", "LVN", "CLINICAL_SUPERVISOR", "DPCS", "DPCS_ADMINISTRATOR"},
    "cti_due_missing": _AGENCY_COMPLIANCE_ROLES | {"RN", "INTAKE_MANAGER", "INTAKE_COORDINATOR"},
    # Certification-record-based state (DRAFT/PENDING_SIGNATURE), distinct
    # from the task-based "due/missing" signal above — the physician-level
    # signer's own queue plus oversight monitoring. Never NP/PA/RN/LVN/
    # DPCS/Administrator signing capability; oversight roles may only
    # monitor per md_signatures_pending_oversight's precedent.
    "cti_pending_signature": (
        set(CTI_SIGNER_ROLES) | {"ADMINISTRATOR", "DPCS", "DPCS_ADMINISTRATOR", "CLINICAL_SUPERVISOR"}
        | COMPLIANCE_OVERSIGHT_ROLES
    ),
    "cti_expiring": (
        set(CTI_SIGNER_ROLES) | _AGENCY_COMPLIANCE_ROLES | {"RN"}
    ),
    "f2f_due_missing": _AGENCY_COMPLIANCE_ROLES | {"RN"},
    "hope_due": set(_AGENCY_COMPLIANCE_ROLES),
    "qies_rejected": set(_AGENCY_COMPLIANCE_ROLES),
    "rnica_incomplete": _AGENCY_COMPLIANCE_ROLES | {"CLINICAL_SUPERVISOR", "RN"},
    "unsigned_visit_notes": _AGENCY_COMPLIANCE_ROLES | {"CLINICAL_SUPERVISOR", "RN", "LVN"},
    "missing_care_plans": _AGENCY_COMPLIANCE_ROLES | {"CLINICAL_SUPERVISOR", "RN"},
    "idg_blockers": _AGENCY_COMPLIANCE_ROLES | {"CLINICAL_SUPERVISOR", "RN", "SW", "CHAPLAIN"},
    "admissions_pipeline": {"ADMINISTRATOR", "DPCS_ADMINISTRATOR", "INTAKE_MANAGER", "INTAKE_COORDINATOR"},
    "referrals": {"ADMINISTRATOR", "DPCS_ADMINISTRATOR", "INTAKE_MANAGER", "INTAKE_COORDINATOR"},
}

# Field-clinician roles only ever see figures scoped to patients assigned to
# them — never agency-wide totals — per the platform's role-visibility model.
# Compliance/QA oversight roles are deliberately excluded: their authority is
# agency-wide monitoring, not an individual caseload.
FIELD_CLINICIAN_ROLES = {"RN", "LVN", "SW", "CHAPLAIN", "VOLUNTEER_COORDINATOR", "CHHA"}

# Every canonical role the widget-visibility engine has deliberately
# considered — including roles whose widget set is intentionally empty
# (e.g. VOLUNTEER_COORDINATOR/CHHA have no compliance_queue widget yet).
# Anything NOT in this set is denied by default (returns no widgets) rather
# than silently falling back to full/unfiltered visibility — an unknown or
# unmapped role must never receive protected compliance data.
CANONICAL_DASHBOARD_ROLES = {
    "ADMINISTRATOR", "DPCS", "DPCS_ADMINISTRATOR", "CLINICAL_SUPERVISOR",
    "MEDICAL_DIRECTOR", "ATTENDING_PHYSICIAN", "HOSPICE_PHYSICIAN", "NP", "PA",
    "RN", "LVN", "SW", "CHAPLAIN", "VOLUNTEER_COORDINATOR", "CHHA",
    "INTAKE_MANAGER", "INTAKE_COORDINATOR",
} | COMPLIANCE_OVERSIGHT_ROLES


def _assigned_patient_ids(db: Session, *, tenant_id: UUID, user_id: UUID) -> set[UUID]:
    """Patients in scope for this user's field-clinician widgets: the union
    of (a) active PatientAssignment rows and (b) patients with a Task
    directly assigned to this user — either relationship is sufficient
    grounds for the user to act on that patient's record."""
    assignment_rows = (
        db.query(PatientAssignment.patient_id)
        .filter(PatientAssignment.tenant_id == tenant_id)
        .filter(PatientAssignment.user_id == user_id)
        .filter(PatientAssignment.active.is_(True))
        .all()
    )
    task_rows = (
        db.query(Task.patient_id)
        .filter(Task.tenant_id == tenant_id)
        .filter(Task.assigned_user_id == user_id)
        .filter(Task.patient_id.isnot(None))
        .all()
    )
    return {row[0] for row in assignment_rows} | {row[0] for row in task_rows}


def _filter_widgets_for_role(queue: dict[str, list[dict[str, Any]]], role: str | None) -> dict[str, list[dict[str, Any]]]:
    """Deny by default: a role must be explicitly present in
    CANONICAL_DASHBOARD_ROLES and in a widget's WIDGET_VISIBILITY set to see
    that widget. An unmapped/unknown role receives no compliance widgets."""
    normalized = normalize_role(role)
    if not normalized or normalized not in CANONICAL_DASHBOARD_ROLES:
        return {priority_key: [] for priority_key in queue}

    filtered: dict[str, list[dict[str, Any]]] = {}
    for priority_key, items in queue.items():
        filtered[priority_key] = [
            item for item in items
            if normalized in WIDGET_VISIBILITY.get(item["key"], set())
        ]
    return filtered


def _build_compliance_queue(
    db: Session,
    *,
    tenant_id: UUID,
    open_tasks: list[Task],
    unsigned_orders: list[DashboardOrderItem],
    clinical_review_orders: list[Any],
    blocked_patients: list[DashboardPatientBlocker],
    role: str | None = None,
    user_id: UUID | None = None,
) -> dict[str, Any]:
    """Real, query-backed counts for the dashboard action queue. Every value
    here is derived directly from live rows (tasks/orders/assessments/notes/
    admissions) — nothing is estimated or hardcoded, since these are
    clinical/regulatory compliance figures."""

    normalized_role = normalize_role(role)
    is_field_scoped = normalized_role in FIELD_CLINICIAN_ROLES and user_id is not None
    is_provider_scoped = physician_identity_service.is_provider_identity_role(normalized_role) and user_id is not None
    scope_patient_ids: set[UUID] | None = None
    if is_field_scoped:
        scope_patient_ids = _assigned_patient_ids(db, tenant_id=tenant_id, user_id=user_id)
    elif is_provider_scoped:
        # Physician Identity Mapping (owner directive 2026-08-21): fail-closed.
        # A provider-identity role (MD/MEDICAL_DIRECTOR/MEDICAL_DIRECTOR_DESIGNEE/
        # ATTENDING_PHYSICIAN/HOSPICE_PHYSICIAN/NP/PA) NEVER gets agency-wide
        # visibility from its role label alone. None here means "verified
        # tenant-wide oversight" (Medical Director/Designee, once linked);
        # an empty set means "deny — no verified linkage yet"; anything
        # else is the assigned-patient scope for a verified Attending
        # Physician/Hospice Physician/NP/PA. See
        # app/services/physician_identity_service.py.
        db_user = db.query(User).filter(User.id == user_id).first()
        scope_patient_ids = (
            physician_identity_service.authorized_patient_ids_for_provider(db, tenant_id=tenant_id, user=db_user)
            if db_user is not None
            else set()
        )

    def _in_scope(patient_id: Any) -> bool:
        if scope_patient_ids is None:
            return True
        try:
            pid = UUID(str(patient_id)) if patient_id is not None else None
        except (ValueError, TypeError):
            pid = patient_id
        return pid in scope_patient_ids

    cti_tasks = [
        task for task in open_tasks
        if _enumish(getattr(task, "task_type", None)).upper() in CTI_TASK_TYPES
        and _in_scope(getattr(task, "patient_id", None))
    ]
    f2f_tasks = [
        task for task in open_tasks
        if _enumish(getattr(task, "task_type", None)).upper() == "F2F"
        and _in_scope(getattr(task, "patient_id", None))
    ]
    care_plan_tasks = [
        task for task in open_tasks
        if _enumish(getattr(task, "task_type", None)).upper() in CARE_PLAN_TASK_TYPES
        and _in_scope(getattr(task, "patient_id", None))
    ]
    scoped_unsigned_orders = [
        order for order in unsigned_orders if _in_scope(getattr(order, "patient_id", None))
    ]
    scoped_clinical_review_orders = [
        order for order in clinical_review_orders if _in_scope(getattr(order, "patient_id", None))
    ]
    scoped_blocked_patients = [
        blocker for blocker in blocked_patients if _in_scope(getattr(blocker, "patient_id", None))
    ]

    cti_pending_query = (
        db.query(Certification)
        .filter(Certification.tenant_id == tenant_id)
        .filter(Certification.status.in_(["DRAFT", "PENDING_SIGNATURE"]))
    )
    if scope_patient_ids is not None:
        cti_pending_query = cti_pending_query.filter(Certification.patient_id.in_(scope_patient_ids))
    cti_pending_signature_count = _safe_count(db, cti_pending_query)

    cti_expiring_query = (
        db.query(Certification)
        .filter(Certification.tenant_id == tenant_id)
        .filter(Certification.status == "FINALIZED")
        .filter(Certification.expires_at.isnot(None))
        .filter(Certification.expires_at <= datetime.utcnow() + timedelta(days=15))
    )
    if scope_patient_ids is not None:
        cti_expiring_query = cti_expiring_query.filter(Certification.patient_id.in_(scope_patient_ids))
    cti_expiring_count = _safe_count(db, cti_expiring_query)

    rnica_query = (
        db.query(RnicaAssessment)
        .filter(RnicaAssessment.tenant_id == tenant_id)
        .filter(RnicaAssessment.locked.is_(False))
    )
    if scope_patient_ids is not None:
        rnica_query = rnica_query.filter(RnicaAssessment.patient_id.in_(scope_patient_ids))
    rnica_incomplete_count = _safe_count(db, rnica_query)

    notes_query = (
        db.query(ClinicalNote)
        .filter(ClinicalNote.tenant_id == tenant_id)
        .filter(ClinicalNote.status == "FINALIZED")
        .filter(ClinicalNote.signed_at.is_(None))
    )
    if scope_patient_ids is not None:
        notes_query = notes_query.filter(ClinicalNote.patient_id.in_(scope_patient_ids))
    unsigned_notes_count = _safe_count(db, notes_query)

    admission_status_counts = Counter(
        _enumish(getattr(admission, "status", None)).upper()
        for admission in (
            db.query(Admission).filter(Admission.tenant_id == tenant_id).all()
        )
    )
    admissions_pipeline = [
        {"status": status, "count": admission_status_counts.get(status, 0)}
        for status in ADMISSION_PIPELINE_STATUSES
    ]
    referrals_count = admission_status_counts.get("REFERRAL", 0)

    priority_1 = [
        {
            "key": "md_signatures_pending_oversight",
            "label": "MD Signatures Pending",
            "value": len(scoped_unsigned_orders),
            "tone": "red",
            "action": "view_queue",
            "action_label": "Review Queue",
        },
        {
            "key": "orders_requiring_provider_signature",
            "label": "Orders Requiring My Signature",
            "value": len(scoped_unsigned_orders),
            "tone": "red",
            "action": "sign",
            "action_label": "Review and Sign",
            "note": (
                "Agency-wide for now — per-physician patient scoping requires a "
                "physician-to-account link not yet in the data model."
            ),
        },
        {
            "key": "cti_due_missing",
            "label": "CTI Due / Missing",
            "value": len(cti_tasks),
            "tone": "red",
        },
        {
            "key": "cti_pending_signature",
            "label": "CTI Pending Signature",
            "value": cti_pending_signature_count,
            "tone": "red",
            "action": "view_queue",
            "action_label": "Review Queue",
        },
        {
            "key": "cti_expiring",
            "label": "CTI Expiring (15 days)",
            "value": cti_expiring_count,
            "tone": "orange",
            "action": "view_queue",
            "action_label": "Review Queue",
        },
        {
            "key": "f2f_due_missing",
            "label": "F2F Due / Missing",
            "value": len(f2f_tasks),
            "tone": "red",
        },
        {
            "key": "hope_due",
            "label": "HOPE Due",
            "value": None,
            "tone": "red",
            "data_available": False,
            "note": "Not yet tracked — no HOPE assessment data source is wired up.",
        },
        {
            "key": "qies_rejected",
            "label": "QIES Rejected",
            "value": None,
            "tone": "red",
            "data_available": False,
            "note": "Not yet tracked — no QIES submission data source is wired up.",
        },
    ]

    priority_2 = [
        {
            "key": "orders_pending_clinical_review",
            "label": "Orders Pending Clinical Review",
            "value": len(scoped_clinical_review_orders),
            "tone": "orange",
            "action": "clinical_review",
            "action_label": "Review Order",
        },
        {
            "key": "orders_requiring_clinical_follow_up",
            "label": "Orders Requiring Clinical Follow-up",
            "value": len(scoped_unsigned_orders),
            "tone": "orange",
            "action": "follow_up",
            "action_label": "Open Follow-up",
        },
        {
            "key": "rnica_incomplete",
            "label": "RNICA Incomplete",
            "value": rnica_incomplete_count,
            "tone": "orange",
        },
        {
            "key": "unsigned_visit_notes",
            "label": "Unsigned Visit Notes",
            "value": unsigned_notes_count,
            "tone": "orange",
        },
        {
            "key": "missing_care_plans",
            "label": "Missing Care Plans",
            "value": len(care_plan_tasks),
            "tone": "orange",
        },
        {
            "key": "idg_blockers",
            "label": "IDG Blockers",
            "value": len(scoped_blocked_patients),
            "tone": "orange",
        },
    ]

    priority_3 = [
        {
            "key": "admissions_pipeline",
            "label": "Admissions Pipeline",
            "value": sum(item["count"] for item in admissions_pipeline),
            "tone": "blue",
            "breakdown": admissions_pipeline,
        },
        {
            "key": "referrals",
            "label": "Referrals",
            "value": referrals_count,
            "tone": "blue",
        },
    ]

    return _filter_widgets_for_role(
        {
            "priority_1": priority_1,
            "priority_2": priority_2,
            "priority_3": priority_3,
        },
        role,
    )


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


def _load_unsigned_orders(db: Session, tenant_id: UUID) -> list[DashboardOrderItem]:
    """Every physician order in this tenant that is NOT yet signed by an MD
    (DRAFT, PENDING_CLINICAL_REVIEW, or PENDING_HOSPICE_MD_APPROVAL) — the
    agency's single view of "which orders are signed vs. not signed" across
    every patient. PENDING_CLINICAL_REVIEW is included here (Phase 1 lifecycle
    expansion, 2026-08-21) since those orders are also not yet MD-signed."""
    return _load_tenant_orders(db, tenant_id, statuses=["DRAFT", "PENDING_CLINICAL_REVIEW", "PENDING_HOSPICE_MD_APPROVAL"])


def _load_orders_pending_clinical_review(db: Session, tenant_id: UUID) -> list[DashboardOrderItem]:
    """Orders conditionally routed to PENDING_CLINICAL_REVIEW — distinct from
    the general unsigned-orders view so RN/clinical-reviewer roles see
    exactly which orders need their review action, separate from orders
    already awaiting physician signature."""
    return _load_tenant_orders(db, tenant_id, statuses=["PENDING_CLINICAL_REVIEW"])


def _load_all_orders(db: Session, tenant_id: UUID, limit: int = 300) -> list[DashboardOrderItem]:
    """Every physician order in this tenant (any status), most recent first —
    the full agency-wide audit trail of signed vs. unsigned orders, capped to
    the most recent `limit` so this stays fast on large charts."""
    return _load_tenant_orders(db, tenant_id, statuses=None, limit=limit, newest_first=True)


def _load_tenant_orders(
    db: Session,
    tenant_id: UUID,
    *,
    statuses: list[str] | None,
    limit: int | None = None,
    newest_first: bool = False,
) -> list[DashboardOrderItem]:
    patient_name = person_name_expression(PatientFaceSheet, Patient.mrn).label("patient_name")

    q = (
        db.query(PhysicianOrder, patient_name)
        .join(Patient, Patient.id == PhysicianOrder.patient_id)
        .outerjoin(PatientFaceSheet, PatientFaceSheet.patient_id == Patient.id)
        .filter(PhysicianOrder.tenant_id == tenant_id)
    )
    if statuses:
        q = q.filter(PhysicianOrder.status.in_(statuses))
    q = q.order_by(PhysicianOrder.ordered_at.desc() if newest_first else PhysicianOrder.ordered_at.asc())
    if limit:
        q = q.limit(limit)
    rows = q.all()

    user_ids = set()
    for order, _ in rows:
        if order.created_by:
            user_ids.add(order.created_by)
        if order.signed_by_user_id:
            user_ids.add(order.signed_by_user_id)
    names_by_id: dict[Any, str] = {}
    if user_ids:
        for row in db.query(User.id, User.full_name, User.display_name).filter(User.id.in_(user_ids)).all():
            names_by_id[row[0]] = row[2] or row[1] or "Unknown"

    return [
        DashboardOrderItem(
            order_id=str(order.id),
            patient_id=str(order.patient_id),
            patient_name=patient_name_val or "Unknown",
            order_category=_enumish(order.order_category),
            order_text=order.order_text,
            status=_enumish(order.status),
            source_type=_enumish(order.source_type),
            ordered_by_provider_name=order.ordered_by_provider_name,
            ordered_by_provider_role=order.ordered_by_provider_role,
            entered_by_name=names_by_id.get(order.created_by),
            ordered_at=_iso(order.ordered_at),
            signed_by_name=names_by_id.get(order.signed_by_user_id) if order.signed_by_user_id else None,
            signed_at=_iso(order.signed_at),
        )
        for order, patient_name_val in rows
    ]


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
    flags = get_note_validation_flags(note)
    return DashboardNoteFlagItem(
        note_id=str(getattr(note, "id")),
        patient_id=str(getattr(note, "patient_id")),
        encounter_date=_iso(getattr(note, "encounter_date", None)),
        discipline=_enumish(getattr(note, "discipline", None)),
        visit_type=_enumish(getattr(note, "visit_type", None)),
        note_category=_enumish(getattr(note, "note_category", None)),
        incident_required=_truthy(flags.get("incident_required", False)),
        incident_status=_enumish(flags.get("incident_status")),
        red_flags=_listish(flags.get("red_flags")),
        needs_clarification=_listish(flags.get("clarification_items")),
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
        # Postgres aborts the whole transaction on a failed statement; without
        # rolling back here, every subsequent query on this session (e.g. the
        # tenant_rows query right after this call in get_owner_dashboard)
        # would also fail with "current transaction is aborted".
        db.rollback()
        return 0


def _safe_count(db: Session, query) -> int:
    """Like _safe_scalar but for an ORM Query object — calls .count() safely."""
    try:
        return query.count()
    except SQLAlchemyError:
        db.rollback()
        return 0


def _task_is_open(task: Task) -> bool:
    status = _enumish(getattr(task, "status", None)).upper()
    return status in {"PENDING", "PENDING", "OVERDUE"}


def _has_flagged_content(note: ClinicalNote) -> bool:
    flags = get_note_validation_flags(note)
    return (
        len(_listish(flags.get("red_flags"))) > 0
        or len(_listish(flags.get("clarification_items"))) > 0
        or _truthy(flags.get("incident_required", False))
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


def _priority_rank(priority: str) -> int:
    priority = (priority or "").upper()
    if priority == "CRITICAL":
        return 3
    if priority == "HIGH":
        return 2
    if priority == "MEDIUM":
        return 1
    return 0


def _task_alert_priority(task: Task) -> str:
    status = _enumish(getattr(task, "status", None)).upper()
    task_type = _enumish(getattr(task, "task_type", None)).upper()
    if status in {"OVERDUE", "ESCALATED"}:
        return "Critical"
    if task_type in {"CLINICAL_REVIEW_REQUIRED", "POC_REVIEW_REQUIRED", "F2F", "IDG_DEFERRED_MD_REVIEW"}:
        return "High"
    return "Medium"


def _incident_alert_priority(incident: IncidentReport) -> str:
    severity = _enumish(getattr(incident, "incident_severity", None)).upper()
    if severity in {"CRITICAL", "SENTINEL"}:
        return "Critical"
    if severity in {"HIGH", "MAJOR"}:
        return "High"
    return "Medium"


def _note_alert_priority(note: ClinicalNote) -> str:
    flags = get_note_validation_flags(note)
    if _truthy(flags.get("incident_required", False)):
        return "High"
    if len(_listish(flags.get("red_flags"))) > 0:
        return "Medium"
    return "Medium"


def _task_alert_title(task: Task) -> str:
    alert_reason = _enumish(getattr(task, "alert_reason", None))
    if alert_reason:
        return alert_reason
    return _enumish(getattr(task, "task_type", None)) or "Task"


def _task_alert_description(task: Task) -> str:
    for field in ("alert_reason", "escalation_reason", "priority", "clinical_severity"):
        value = getattr(task, field, None)
        if value:
            return str(value)
    return _enumish(getattr(task, "task_type", None)) or "Open task requires review."


def _incident_alert_description(incident: IncidentReport) -> str:
    for field in ("narrative", "place", "area", "injury_type", "other_injury_text"):
        value = getattr(incident, field, None)
        if value:
            text_value = str(value).strip()
            if text_value:
                return text_value
    return _enumish(getattr(incident, "incident_type", None)) or "Incident requires review."


def _note_alert_description(note: ClinicalNote) -> str:
    flags = get_note_validation_flags(note)
    red_flags = _listish(flags.get("red_flags"))
    if red_flags:
        return red_flags[0]
    clarification = _listish(flags.get("clarification_items"))
    if clarification:
        return clarification[0]
    content = str(getattr(note, "content", "") or "").strip()
    return content[:120] if content else "Clinical note requires review."

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
