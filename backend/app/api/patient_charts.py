from __future__ import annotations

from datetime import datetime, date, timedelta
from types import SimpleNamespace
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.patient import Patient
from app.models.certification import Certification
from app.models.f2f_encounter import F2FEncounter
from app.models.task import Task
from app.models.user import User
from app.models.communications_log import CommunicationsLog
from app.models.incident_report import IncidentReport
from app.models.clinical_note import ClinicalNote
from app.models.patient_assignment import PatientAssignment
from app.models.enums import Discipline, TaskStatus, TaskType
from app.services.bereavement_aggregation_engine import (
    BereavementAggregationEngine,
    BereavementNoteInput,
)
from app.services.eligibility.engine import evaluate_hospice_eligibility


router = APIRouter(prefix="/patient-charts", tags=["patient-charts"])

bereavement_engine = BereavementAggregationEngine()


def _load_patient(db: Session, patient_id: UUID) -> Patient:
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


def _patient_namespace(patient: Patient) -> SimpleNamespace:
    return SimpleNamespace(
        id=patient.id,
        tenant_id=patient.tenant_id,
        primary_diagnosis_description=patient.primary_diagnosis,
        primary_diagnosis_code=None,
        secondary_diagnoses=[],
    )


def _serialize_datetime(value):
    return value.isoformat() if value else None


def _serialize_date(value):
    return value.isoformat() if value else None


def _enum_value(value):
    return value.value if hasattr(value, "value") else value


def _base_patient(patient: Patient) -> dict:
    return {
        "id": str(patient.id),
        "mrn": patient.mrn,
        "full_name": patient.full_name,
        "primary_diagnosis": patient.primary_diagnosis,
        "status": patient.status,
        "acuity_state": patient.acuity_state,
        "admission_status": patient.admission_status,
        "hospice_election_date": _serialize_date(patient.hospice_election_date),
        "soc_date": _serialize_datetime(patient.soc_date),
    }


def _count_by(items: list[dict], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        value = item.get(key) or "Unknown"
        counts[value] = counts.get(value, 0) + 1
    return counts


def _load_visit_rows(db: Session, patient_id: UUID, *, limit: int | None = None, ascending: bool = True):
    order = "ASC" if ascending else "DESC"
    sql = f"""
        SELECT
            v.id,
            v.visit_datetime,
            v.visit_type,
            v.visit_discipline,
            v.status,
            v.is_supervisory,
            u.full_name AS provider_name
        FROM visits v
        JOIN users u ON u.id = v.provider_id
        WHERE v.patient_id = :patient_id
        ORDER BY v.visit_datetime {order}
    """
    if limit is not None:
        sql += " LIMIT :limit"

    params = {"patient_id": patient_id}
    if limit is not None:
        params["limit"] = limit

    return db.execute(text(sql), params).mappings().all()


@router.get("/{patient_id}/summary")
def get_patient_chart_summary(patient_id: UUID, db: Session = Depends(get_db)):
    patient = _load_patient(db, patient_id)

    communication_rows = (
        db.query(CommunicationsLog)
        .filter(CommunicationsLog.patient_id == patient.id)
        .order_by(CommunicationsLog.event_time.desc(), CommunicationsLog.created_at.desc())
        .limit(5)
        .all()
    )

    incident_rows = (
        db.query(IncidentReport)
        .filter(IncidentReport.patient_id == patient.id)
        .order_by(IncidentReport.incident_date.desc(), IncidentReport.created_at.desc())
        .limit(5)
        .all()
    )

    visit_rows = _load_visit_rows(db, patient.id, limit=8, ascending=False)

    assignment_rows = (
        db.query(PatientAssignment, User.full_name.label("staff_name"))
        .join(User, User.id == PatientAssignment.user_id)
        .filter(PatientAssignment.patient_id == patient.id)
        .filter(PatientAssignment.active.is_(True))
        .order_by(PatientAssignment.is_primary.desc(), PatientAssignment.assigned_at.desc())
        .all()
    )

    return {
        "patient": _base_patient(patient),
        "care_team": [
            {
                "discipline": row.PatientAssignment.discipline.value if hasattr(row.PatientAssignment.discipline, "value") else str(row.PatientAssignment.discipline),
                "staff_name": row.staff_name,
                "primary": bool(row.PatientAssignment.is_primary),
                "status": row.PatientAssignment.status,
                "service_area": row.PatientAssignment.service_area,
            }
            for row in assignment_rows
        ],
        "recent_visits": [
            {
                "id": str(visit["id"]),
                "visit_datetime": _serialize_datetime(visit["visit_datetime"]),
                "visit_type": visit["visit_type"],
                "discipline": visit["visit_discipline"],
                "status": visit["status"],
                "provider_name": visit["provider_name"],
            }
            for visit in visit_rows
        ],
        "communication_summary": {
            "total": db.query(func.count(CommunicationsLog.id))
            .filter(CommunicationsLog.patient_id == patient.id)
            .scalar()
            or 0,
            "latest": [
                {
                    "id": str(row.id),
                    "event_type": row.event_type,
                    "focus_area": row.focus_area,
                    "event_time": _serialize_datetime(row.event_time),
                    "summary": row.summary,
                    "status": row.status,
                }
                for row in communication_rows
            ],
        },
        "incident_summary": {
            "total": db.query(func.count(IncidentReport.id))
            .filter(IncidentReport.patient_id == patient.id)
            .scalar()
            or 0,
            "latest": [
                {
                    "id": str(row.id),
                    "incident_type": row.incident_type,
                    "incident_severity": row.incident_severity,
                    "incident_date": _serialize_date(row.incident_date),
                    "reported_date": _serialize_date(row.reported_date),
                    "narrative": row.narrative,
                }
                for row in incident_rows
            ],
        },
        "compliance_summary": get_patient_compliance(patient_id, db),
        "volunteer_summary": get_patient_volunteer_schedule(patient_id, db),
    }


@router.get("/{patient_id}/physician")
def get_patient_physician_summary(patient_id: UUID, db: Session = Depends(get_db)):
    patient = _load_patient(db, patient_id)

    certifications = (
        db.query(Certification)
        .filter(Certification.patient_id == patient.id)
        .order_by(Certification.signed_at.desc())
        .all()
    )

    f2f_encounters = (
        db.query(F2FEncounter)
        .filter(F2FEncounter.patient_id == patient.id)
        .order_by(F2FEncounter.encounter_date.desc(), F2FEncounter.created_at.desc())
        .all()
    )

    return {
        "patient": _base_patient(patient),
        "metrics": [
            {"label": "CTI / Certifications", "value": len(certifications)},
            {"label": "F2F encounters", "value": len(f2f_encounters)},
            {
                "label": "Finalized F2F",
                "value": sum(1 for row in f2f_encounters if (row.status or "").upper() == "FINALIZED"),
            },
        ],
        "cti": [
            {
                "id": str(row.id),
                "cert_type": row.cert_type,
                "signed_at": _serialize_datetime(row.signed_at),
                "effective_date": _serialize_date(row.effective_date),
                "signed_by_role": row.signed_by_role,
                "status": row.status,
            }
            for row in certifications
        ],
        "f2f": [
            {
                "id": str(row.id),
                "encounter_date": _serialize_date(row.encounter_date),
                "performed_by_role": row.performed_by_role,
                "status": row.status,
                "finalized_at": _serialize_datetime(row.finalized_at),
                "summary": row.summary,
                "clinical_decline_summary": row.clinical_decline_summary,
            }
            for row in f2f_encounters
        ],
    }


@router.get("/{patient_id}/communication-log")
def get_patient_communication_log(patient_id: UUID, db: Session = Depends(get_db)):
    _load_patient(db, patient_id)

    rows = (
        db.query(CommunicationsLog)
        .filter(CommunicationsLog.patient_id == patient_id)
        .order_by(CommunicationsLog.event_time.desc(), CommunicationsLog.created_at.desc())
        .all()
    )

    return {
        "total": len(rows),
        "counts_by_type": _count_by(
            [{"event_type": row.event_type} for row in rows],
            "event_type",
        ),
        "entries": [
            {
                "id": str(row.id),
                "event_type": row.event_type,
                "focus_area": row.focus_area,
                "event_time": _serialize_datetime(row.event_time),
                "summary": row.summary,
                "details": row.details,
                "status": row.status,
                "created_at": _serialize_datetime(row.created_at),
            }
            for row in rows
        ],
    }


@router.get("/{patient_id}/incident-occurrence")
def get_patient_incident_occurrences(patient_id: UUID, db: Session = Depends(get_db)):
    _load_patient(db, patient_id)

    rows = (
        db.query(IncidentReport)
        .filter(IncidentReport.patient_id == patient_id)
        .order_by(IncidentReport.incident_date.desc(), IncidentReport.created_at.desc())
        .all()
    )

    items = [
        {
            "id": str(row.id),
            "incident_type": row.incident_type,
            "incident_severity": row.incident_severity,
            "incident_date": _serialize_date(row.incident_date),
            "reported_date": _serialize_date(row.reported_date),
            "incident_time": row.incident_time.isoformat() if row.incident_time else None,
            "reported_by": row.reported_by,
            "witnessed_by": row.witnessed_by,
            "place": row.place,
            "area": row.area,
            "surface": row.surface,
            "medication_used": row.medication_used,
            "activity_at_time": row.activity_at_time,
            "injury_level": row.injury_level,
            "injury_type": row.injury_type,
            "other_injury_text": row.other_injury_text,
            "narrative": row.narrative,
            "signed_at": _serialize_datetime(row.signed_at),
        }
        for row in rows
    ]

    return {
        "total": len(items),
        "counts_by_type": _count_by(items, "incident_type"),
        "counts_by_severity": _count_by(items, "incident_severity"),
        "items": items,
    }


@router.get("/{patient_id}/bereavement")
def get_patient_bereavement(patient_id: UUID, db: Session = Depends(get_db)):
    patient = _load_patient(db, patient_id)

    note_rows = (
        db.query(ClinicalNote)
        .filter(ClinicalNote.patient_id == patient.id)
        .order_by(ClinicalNote.created_at.desc())
        .all()
    )

    comm_rows = (
        db.query(CommunicationsLog)
        .filter(CommunicationsLog.patient_id == patient.id)
        .order_by(CommunicationsLog.event_time.desc(), CommunicationsLog.created_at.desc())
        .all()
    )

    notes = [
        BereavementNoteInput(
            patient_id=patient.id,
            note_id=row.id,
            discipline=(row.discipline or ""),
            text=(row.content or ""),
        )
        for row in note_rows
    ]
    result = bereavement_engine.detect(notes)

    relevant_comms = [
        {
            "id": str(row.id),
            "event_type": row.event_type,
            "event_time": _serialize_datetime(row.event_time),
            "summary": row.summary,
            "status": row.status,
        }
        for row in comm_rows
        if "bereav" in (row.event_type or "").lower()
        or "grief" in (row.summary or "").lower()
        or "loss" in (row.summary or "").lower()
        or "mourning" in (row.summary or "").lower()
    ]

    return {
        "patient": _base_patient(patient),
        "aggregation": {
            "rn_present": result.rn_present,
            "sw_present": result.sw_present,
            "chaplain_present": result.chaplain_present,
            "reason_codes": result.reason_codes,
            "source_notes": [str(note_id) for note_id in result.source_notes],
        },
        "supporting_notes": [
            {
                "id": str(row.id),
                "discipline": row.discipline,
                "form_key": row.form_key,
                "created_at": _serialize_datetime(row.created_at),
                "content": row.content,
            }
            for row in note_rows[:10]
            if row.content
        ],
        "supporting_communications": relevant_comms[:10],
    }


@router.get("/{patient_id}/compliance")
def get_patient_compliance(patient_id: UUID, db: Session = Depends(get_db)):
    patient = _load_patient(db, patient_id)
    patient_ctx = _patient_namespace(patient)

    eligibility = evaluate_hospice_eligibility(patient_ctx, date.today().isoformat())

    task_rows = (
        db.query(Task)
        .filter(Task.patient_id == patient.id)
        .all()
    )

    note_rows = (
        db.query(ClinicalNote)
        .filter(ClinicalNote.patient_id == patient.id)
        .order_by(ClinicalNote.created_at.desc())
        .all()
    )

    hope_notes = [row for row in note_rows if (row.form_key or "").upper().startswith("HOPE")]
    poc_notes = [row for row in note_rows if (row.form_key or "").upper().find("POC") >= 0]
    f2f_notes = [row for row in note_rows if (row.form_key or "").upper().find("F2F") >= 0]

    task_counts = {
        "pending": sum(1 for row in task_rows if _enum_value(row.status) == "PENDING"),
        "overdue": sum(1 for row in task_rows if _enum_value(row.status) == "OVERDUE"),
        "completed": sum(1 for row in task_rows if _enum_value(row.status) == "COMPLETED"),
    }

    open_issues = []
    if task_counts["pending"] or task_counts["overdue"]:
        open_issues.append("Open workflow tasks")
    if not hope_notes:
        open_issues.append("HOPE notes not yet documented")
    if not f2f_notes:
        open_issues.append("F2F note not yet documented")

    return {
        "patient": _base_patient(patient),
        "eligibility": eligibility,
        "task_counts": task_counts,
        "note_counts": {
            "total": len(note_rows),
            "hope": len(hope_notes),
            "poc": len(poc_notes),
            "f2f": len(f2f_notes),
        },
        "hope_status": "READY" if hope_notes else "NOT_STARTED",
        "qies_status": "READY" if eligibility.get("eligible") and task_counts["pending"] == 0 else "NEEDS_REVIEW",
        "open_issues": open_issues,
        "recent_notes": [
            {
                "id": str(row.id),
                "form_key": row.form_key,
                "note_type": row.note_type,
                "status": row.status,
                "created_at": _serialize_datetime(row.created_at),
                "content": row.content,
            }
            for row in note_rows[:5]
        ],
    }


@router.get("/{patient_id}/volunteer-scheduling")
def get_patient_volunteer_schedule(patient_id: UUID, db: Session = Depends(get_db)):
    patient = _load_patient(db, patient_id)

    visit_rows = _load_visit_rows(db, patient.id, ascending=True)

    assignment_rows = (
        db.query(PatientAssignment, User.full_name.label("staff_name"))
        .join(User, User.id == PatientAssignment.user_id)
        .filter(PatientAssignment.patient_id == patient.id)
        .filter(
            PatientAssignment.discipline.in_([
                Discipline.VOLUNTEER,
                Discipline.VOLUNTEER_COORDINATOR,
            ])
        )
        .order_by(PatientAssignment.assigned_at.desc())
        .all()
    )

    task_rows = (
        db.query(Task)
        .filter(Task.patient_id == patient.id)
        .filter(Task.task_type.in_([TaskType.HUV, TaskType.OTHER]))
        .order_by(Task.due_date.asc())
        .all()
    )

    return {
        "patient": _base_patient(patient),
        "visits": [
            {
                "id": str(visit["id"]),
                "visit_datetime": _serialize_datetime(visit["visit_datetime"]),
                "visit_type": visit["visit_type"],
                "visit_discipline": visit["visit_discipline"],
                "status": visit["status"],
                "provider_name": visit["provider_name"],
                "is_supervisory": bool(visit["is_supervisory"]),
            }
            for visit in visit_rows
        ],
        "assignments": [
            {
                "id": str(row.PatientAssignment.id),
                "discipline": row.PatientAssignment.discipline.value if hasattr(row.PatientAssignment.discipline, "value") else str(row.PatientAssignment.discipline),
                "staff_name": row.staff_name,
                "primary": bool(row.PatientAssignment.is_primary),
                "service_area": row.PatientAssignment.service_area,
                "status": row.PatientAssignment.status,
                "assigned_at": _serialize_datetime(row.PatientAssignment.assigned_at),
            }
            for row in assignment_rows
        ],
        "task_slots": [
            {
                "id": str(row.id),
                "task_type": _enum_value(row.task_type),
                "status": _enum_value(row.status),
                "due_date": _serialize_date(row.due_date),
                "assigned_user_id": str(row.assigned_user_id) if row.assigned_user_id else None,
                "assigned_role": row.assigned_role,
                "alert_reason": row.alert_reason,
            }
            for row in task_rows
        ],
    }
