# app/api/referrals.py

"""
Incoming referral intake review queue.

Referral creation is intentionally decoupled from Patient creation: staff
submit intake data via POST /referrals, which lands as a PENDING record with
no clinical record yet. A separate reviewer then either accepts it (which
converts it into a full Patient + PatientFaceSheet + PatientDiagnosis +
Admission bundle, via the exact same conversion used to power the legacy
direct-create endpoint) or declines it with a required reason. Both actions
are permanently recorded (reviewed_by/reviewed_at) for audit purposes.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.patients import (
    ReferralFaceSheetCreate,
    build_patient_from_referral_payload,
    get_db_with_request_state,
    require_tenant_user,
    _tenant_id_uuid,
)
from app.models.referral import Referral
from app.services.audit_logger import log_event

router = APIRouter(prefix="/referrals", tags=["referrals"])

REFERRAL_FIELDS = list(ReferralFaceSheetCreate.model_fields.keys())


def _serialize(referral: Referral) -> dict:
    return {
        "id": str(referral.id),
        "status": referral.status,
        "first_name": referral.first_name,
        "middle_name": referral.middle_name,
        "last_name": referral.last_name,
        "date_of_birth": referral.date_of_birth,
        "phone": referral.phone,
        "address": referral.address,
        "city": referral.city,
        "state": referral.state,
        "zip": referral.zip,
        "gender": referral.gender,
        "language": referral.language,
        "religion": referral.religion,
        "marital_status": referral.marital_status,
        "primary_payer": referral.primary_payer,
        "primary_policy_number": referral.primary_policy_number,
        "authorization_status": referral.authorization_status,
        "current_level_of_care": referral.current_level_of_care,
        "primary_diagnosis": referral.primary_diagnosis,
        "secondary_diagnoses": referral.secondary_diagnoses,
        "attending_physician_name": referral.attending_physician_name,
        "attending_physician_npi": referral.attending_physician_npi,
        "responsible_party_name": referral.responsible_party_name,
        "responsible_party_relationship": referral.responsible_party_relationship,
        "responsible_party_phone": referral.responsible_party_phone,
        "emergency_contact_name": referral.emergency_contact_name,
        "emergency_contact_relationship": referral.emergency_contact_relationship,
        "emergency_contact_phone": referral.emergency_contact_phone,
        "referral_source": referral.referral_source,
        "referral_date": referral.referral_date,
        "special_instructions": referral.special_instructions,
        "decline_reason": referral.decline_reason,
        "converted_patient_id": str(referral.converted_patient_id) if referral.converted_patient_id else None,
        "created_by": str(referral.created_by) if referral.created_by else None,
        "created_at": referral.created_at,
        "reviewed_by": str(referral.reviewed_by) if referral.reviewed_by else None,
        "reviewed_at": referral.reviewed_at,
    }


class ReferralDecline(BaseModel):
    reason: str


@router.post("")
def create_referral(
    payload: ReferralFaceSheetCreate,
    db: Session = Depends(get_db_with_request_state),
    user=Depends(require_tenant_user),
):
    tenant_id = _tenant_id_uuid(user)
    user_id = getattr(user, "user_id", None)
    if not user_id:
        raise HTTPException(500, "Invalid user identity")

    referral = Referral(
        tenant_id=tenant_id,
        created_by=user_id,
        **{field: getattr(payload, field) for field in REFERRAL_FIELDS},
    )
    db.add(referral)
    db.commit()
    db.refresh(referral)

    log_event(db=db, tenant_id=str(tenant_id), user_id=str(user_id), action="REFERRAL_CREATED", entity_type="Referral", entity_id=str(referral.id), metadata={"referral_source": referral.referral_source})

    return _serialize(referral)


@router.get("")
def list_referrals(
    status_filter: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db_with_request_state),
    user=Depends(require_tenant_user),
):
    tenant_id = _tenant_id_uuid(user)
    query = db.query(Referral).filter(Referral.tenant_id == tenant_id)
    if status_filter:
        query = query.filter(Referral.status == status_filter.upper())
    referrals = query.order_by(Referral.created_at.desc()).all()
    return [_serialize(referral) for referral in referrals]


@router.get("/{referral_id}")
def get_referral(
    referral_id: str,
    db: Session = Depends(get_db_with_request_state),
    user=Depends(require_tenant_user),
):
    tenant_id = _tenant_id_uuid(user)
    referral = (
        db.query(Referral)
        .filter(Referral.id == uuid.UUID(referral_id), Referral.tenant_id == tenant_id)
        .first()
    )
    if not referral:
        raise HTTPException(404, "Referral not found")
    return _serialize(referral)


@router.post("/{referral_id}/accept")
def accept_referral(
    referral_id: str,
    db: Session = Depends(get_db_with_request_state),
    user=Depends(require_tenant_user),
):
    tenant_id = _tenant_id_uuid(user)
    user_id = getattr(user, "user_id", None)
    if not user_id:
        raise HTTPException(500, "Invalid user identity")

    referral = (
        db.query(Referral)
        .filter(Referral.id == uuid.UUID(referral_id), Referral.tenant_id == tenant_id)
        .first()
    )
    if not referral:
        raise HTTPException(404, "Referral not found")
    if referral.status != "PENDING":
        raise HTTPException(400, f"Referral is already {referral.status}, cannot accept")

    payload = ReferralFaceSheetCreate(**{field: getattr(referral, field) for field in REFERRAL_FIELDS})
    result = build_patient_from_referral_payload(db, tenant_id=tenant_id, user_id=user_id, payload=payload)

    referral.status = "ACCEPTED"
    referral.converted_patient_id = uuid.UUID(result["id"])
    referral.reviewed_by = user_id
    referral.reviewed_at = datetime.now(timezone.utc)
    db.add(referral)
    db.commit()

    log_event(db=db, tenant_id=str(tenant_id), user_id=str(user_id), action="REFERRAL_ACCEPTED", entity_type="Referral", entity_id=str(referral.id), metadata={"converted_patient_id": result["id"]})

    return result


@router.post("/{referral_id}/decline")
def decline_referral(
    referral_id: str,
    payload: ReferralDecline,
    db: Session = Depends(get_db_with_request_state),
    user=Depends(require_tenant_user),
):
    tenant_id = _tenant_id_uuid(user)
    user_id = getattr(user, "user_id", None)
    if not user_id:
        raise HTTPException(500, "Invalid user identity")
    if not payload.reason or not payload.reason.strip():
        raise HTTPException(422, "A decline reason is required")

    referral = (
        db.query(Referral)
        .filter(Referral.id == uuid.UUID(referral_id), Referral.tenant_id == tenant_id)
        .first()
    )
    if not referral:
        raise HTTPException(404, "Referral not found")
    if referral.status != "PENDING":
        raise HTTPException(400, f"Referral is already {referral.status}, cannot decline")

    referral.status = "DECLINED"
    referral.decline_reason = payload.reason.strip()
    referral.reviewed_by = user_id
    referral.reviewed_at = datetime.now(timezone.utc)
    db.add(referral)
    db.commit()
    db.refresh(referral)

    log_event(db=db, tenant_id=str(tenant_id), user_id=str(user_id), action="REFERRAL_DECLINED", entity_type="Referral", entity_id=str(referral.id), metadata={"reason": referral.decline_reason})

    return _serialize(referral)

