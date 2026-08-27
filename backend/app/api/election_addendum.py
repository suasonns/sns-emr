from __future__ import annotations

"""
Real Election Statement Addendum (42 CFR 418.24(b)) request/delivery
tracking -- the actual furnishing-deadline compliance clock, not just a
UI note. See app.billing.services.election_addendum_service for the CMS
5-day / 72-hour rule this evaluates against.
"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.patient import Patient
from app.billing.models.election_addendum_request import ElectionAddendumRequest
from app.billing.services.election_addendum_service import (
    ElectionAddendumComplianceError,
    compute_addendum_compliance,
)

router = APIRouter(prefix="/patients", tags=["Election Addendum"])


class ElectionAddendumCreate(BaseModel):
    requested_date: date
    requested_by: str


class ElectionAddendumUpdate(BaseModel):
    delivered_date: date | None = None
    not_required_reason: str | None = None


class ElectionAddendumResponse(BaseModel):
    id: str
    requested_date: str
    requested_by: str
    delivered_date: str | None
    not_required_reason: str | None
    deadline_days: int
    deadline_date: str
    is_satisfied: bool
    is_late: bool
    is_waived_by_early_discharge: bool
    reason: str | None


VALID_REQUESTED_BY = {"PATIENT_OR_REPRESENTATIVE", "NON_HOSPICE_PROVIDER", "MEDICARE_CONTRACTOR"}


def _get_patient(db: Session, patient_id: str) -> Patient:
    patient = db.get(Patient, patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


def _resolve_election_date(patient: Patient) -> date:
    if patient.hospice_election_date is None:
        raise HTTPException(
            status_code=409,
            detail="Patient has no hospice_election_date on file; cannot evaluate the addendum deadline.",
        )
    return patient.hospice_election_date


def _discharge_or_death_date(patient: Patient) -> date | None:
    status = (patient.status or "").upper()
    if status in ("DECEASED", "DISCHARGED"):
        return patient.discharge_date
    return None


def _serialize(row: ElectionAddendumRequest, patient: Patient) -> dict:
    election_date = _resolve_election_date(patient)
    compliance = compute_addendum_compliance(
        election_date=election_date,
        requested_date=row.requested_date,
        delivered_date=row.delivered_date,
        discharge_or_death_date=_discharge_or_death_date(patient),
        not_required_reason=row.not_required_reason,
    )
    return {
        "id": str(row.id),
        "requested_date": row.requested_date.isoformat(),
        "requested_by": row.requested_by,
        "delivered_date": row.delivered_date.isoformat() if row.delivered_date else None,
        "not_required_reason": row.not_required_reason,
        "deadline_days": compliance.deadline_days,
        "deadline_date": compliance.deadline_date.isoformat(),
        "is_satisfied": compliance.is_satisfied,
        "is_late": compliance.is_late,
        "is_waived_by_early_discharge": compliance.is_waived_by_early_discharge,
        "reason": compliance.reason,
    }


@router.post(
    "/{patient_id}/election-addendum-requests",
    response_model=ElectionAddendumResponse,
    summary="Log a real Election Statement Addendum request and start the CMS furnishing-deadline clock",
    operation_id="CreateElectionAddendumRequest",
)
def create_election_addendum_request(
    patient_id: str,
    payload: ElectionAddendumCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if payload.requested_by not in VALID_REQUESTED_BY:
        raise HTTPException(
            status_code=422,
            detail=f"requested_by must be one of {sorted(VALID_REQUESTED_BY)}",
        )

    patient = _get_patient(db, patient_id)
    _resolve_election_date(patient)  # fail fast if election_date missing

    tenant_id = getattr(current_user, "tenant_id", None)
    user_id = getattr(current_user, "id", None)
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Missing tenant")

    row = ElectionAddendumRequest(
        tenant_id=tenant_id,
        patient_id=patient_id,
        requested_date=payload.requested_date,
        requested_by=payload.requested_by,
        created_by=user_id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    try:
        return _serialize(row, patient)
    except ElectionAddendumComplianceError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get(
    "/{patient_id}/election-addendum-requests",
    response_model=list[ElectionAddendumResponse],
    summary="List real Election Statement Addendum requests and their real-time compliance status",
    operation_id="ListElectionAddendumRequests",
)
def list_election_addendum_requests(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    patient = _get_patient(db, patient_id)
    rows = (
        db.query(ElectionAddendumRequest)
        .filter(ElectionAddendumRequest.patient_id == patient_id)
        .order_by(ElectionAddendumRequest.requested_date.desc())
        .all()
    )
    return [_serialize(row, patient) for row in rows]


@router.patch(
    "/{patient_id}/election-addendum-requests/{request_id}",
    response_model=ElectionAddendumResponse,
    summary="Record the real delivery date (or a documented waiver reason) for an addendum request",
    operation_id="UpdateElectionAddendumRequest",
)
def update_election_addendum_request(
    patient_id: str,
    request_id: str,
    payload: ElectionAddendumUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    patient = _get_patient(db, patient_id)
    row = (
        db.query(ElectionAddendumRequest)
        .filter(
            ElectionAddendumRequest.id == request_id,
            ElectionAddendumRequest.patient_id == patient_id,
        )
        .first()
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Election addendum request not found")

    row.delivered_date = payload.delivered_date
    row.not_required_reason = payload.not_required_reason
    db.add(row)
    db.commit()
    db.refresh(row)

    return _serialize(row, patient)
