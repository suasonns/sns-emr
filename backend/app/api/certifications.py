# app/api/certifications.py

"""
Certification of Terminal Illness (CTI) / Recertification endpoints, per
the Phase 1 lifecycle expansion (owner directive 2026-08-21, additive-only):

    DRAFT -> PENDING_SIGNATURE -> FINALIZED -> [SUPERSEDED by next cert]

CTI is a physician CERTIFICATION workflow, strictly separate from the F2F
ENCOUNTER workflow (app/api/f2f.py) — signing authority is never combined
or inferred between the two. Any clinical role may prepare a draft
narrative/evidence packet; only CTI_SIGNER_ROLES (Attending Physician,
Medical Director, Medical Director Designee, Hospice Physician) may sign.
NP, PA, RN, LVN, DPCS, and Administrator may never sign a CTI — enforced
both at this endpoint gate (allow_clinical_admin=False) and again, as
defense in depth, inside certification_service.sign_certification().
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.patient_access import get_authorized_patient
from app.core.permissions import require_roles
from app.core.security import CurrentUser
from app.models.certification import Certification
from app.models.patient import Patient
from app.models.user import User
from app.services import certification_service as svc
from app.services.audit_logger import log_event

router = APIRouter(prefix="/certifications", tags=["Certifications"])

# Any clinical role may prepare/view a CTI draft; only CTI_SIGNER_ROLES
# (physician-level) may sign it — see require_roles(..., allow_clinical_admin=False)
# on the /sign endpoint below.
CLINICAL_ROLES = ["LVN", "RN", "NP", "PA", "MD", "MEDICAL_DIRECTOR", "ATTENDING_PHYSICIAN", "HOSPICE_PHYSICIAN"]


class CertDraftCreate(BaseModel):
    benefit_period_id: uuid.UUID
    physician_narrative: str
    supporting_evidence: str | None = None
    clinical_decline_indicators: str | None = None


class CertNarrativeUpdate(BaseModel):
    physician_narrative: str | None = None
    supporting_evidence: str | None = None
    clinical_decline_indicators: str | None = None


def _user_name_map(db: Session, user_ids: set) -> dict:
    ids = {uid for uid in user_ids if uid}
    if not ids:
        return {}
    rows = db.query(User.id, User.full_name, User.display_name).filter(User.id.in_(ids)).all()
    return {row[0]: (row[2] or row[1] or "Unknown") for row in rows}


def _name_ids(cert: Certification) -> set:
    return {cert.created_by, cert.narrative_by, cert.signed_by_user_id}


def _serialize(cert: Certification, name_map: dict | None = None) -> dict:
    name_map = name_map or {}
    return {
        "id": str(cert.id),
        "patient_id": str(cert.patient_id),
        "benefit_period_id": str(cert.benefit_period_id),
        "cert_type": cert.cert_type,
        "status": cert.status,
        "status_label": svc.label_for(cert.status),
        "physician_narrative": cert.physician_narrative,
        "supporting_evidence": cert.supporting_evidence,
        "clinical_decline_indicators": cert.clinical_decline_indicators,
        "narrative_by": str(cert.narrative_by) if cert.narrative_by else None,
        "narrative_by_name": name_map.get(cert.narrative_by),
        "narrative_at": cert.narrative_at.isoformat() if cert.narrative_at else None,
        "signed_by_user_id": str(cert.signed_by_user_id) if cert.signed_by_user_id else None,
        "signed_by_name": name_map.get(cert.signed_by_user_id),
        "signed_by_role": cert.signed_by_role or None,
        "signed_at": cert.signed_at.isoformat() if cert.signed_at and cert.status == "FINALIZED" else None,
        "effective_date": cert.effective_date.isoformat() if cert.effective_date else None,
        "expires_at": cert.expires_at.isoformat() if cert.expires_at else None,
        "superseded_by_id": str(cert.superseded_by_id) if cert.superseded_by_id else None,
        "superseded_at": cert.superseded_at.isoformat() if cert.superseded_at else None,
        "created_by": str(cert.created_by) if cert.created_by else None,
        "created_by_name": name_map.get(cert.created_by),
        "created_at": cert.created_at.isoformat() if cert.created_at else None,
    }


def _get_patient_or_404(db: Session, patient_id: uuid.UUID, user: CurrentUser) -> Patient:
    return get_authorized_patient(db, patient_id, user)


def _get_cert_or_404(db: Session, certification_id: uuid.UUID, user: CurrentUser) -> Certification:
    cert = svc.get_certification(db, tenant_id=user.tenant_id, certification_id=certification_id)
    if not cert:
        raise HTTPException(status_code=404, detail="Certification not found")
    get_authorized_patient(db, cert.patient_id, user)
    return cert


@router.get("/patients/{patient_id}", summary="List a patient's certifications (CTI/Recert)")
def list_certifications(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(CLINICAL_ROLES)),
):
    _get_patient_or_404(db, patient_id, user)
    certs = svc.list_certifications(db, tenant_id=user.tenant_id, patient_id=patient_id)
    ids = set()
    for c in certs:
        ids.update(_name_ids(c))
    name_map = _user_name_map(db, ids)
    return [_serialize(c, name_map) for c in certs]


@router.get("/{certification_id}/status-history", summary="Immutable status-transition audit trail for a CTI")
def certification_status_history(
    certification_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(CLINICAL_ROLES)),
):
    cert = _get_cert_or_404(db, certification_id, user)
    events = svc.get_status_history(db, tenant_id=user.tenant_id, certification_id=cert.id)
    ids = {e.changed_by_user_id for e in events if e.changed_by_user_id}
    name_map = _user_name_map(db, ids)
    return [
        {
            "id": str(e.id),
            "from_status": e.from_status,
            "from_status_label": svc.label_for(e.from_status) if e.from_status else None,
            "to_status": e.to_status,
            "to_status_label": svc.label_for(e.to_status),
            "changed_by_user_id": str(e.changed_by_user_id) if e.changed_by_user_id else None,
            "changed_by_name": name_map.get(e.changed_by_user_id),
            "changed_by_role": e.changed_by_role,
            "changed_at": e.changed_at.isoformat() if e.changed_at else None,
            "reason": e.reason,
            "automatic": e.automatic,
            "evidence": e.evidence,
        }
        for e in events
    ]


@router.post("/patients/{patient_id}/draft", summary="Create a DRAFT certification with physician narrative + LCD evidence")
def create_draft(
    patient_id: uuid.UUID,
    payload: CertDraftCreate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(CLINICAL_ROLES)),
):
    _get_patient_or_404(db, patient_id, user)
    try:
        cert = svc.create_draft(
            db, tenant_id=user.tenant_id, patient_id=patient_id,
            benefit_period_id=payload.benefit_period_id,
            physician_narrative=payload.physician_narrative,
            supporting_evidence=payload.supporting_evidence,
            clinical_decline_indicators=payload.clinical_decline_indicators,
            created_by=user.user_id, created_by_role=user.role,
        )
    except svc.CertificationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)

    log_event(
        db=db, tenant_id=str(user.tenant_id), user_id=user.user_id, role=user.role,
        action="CREATE_CTI_DRAFT", entity_type="certification", entity_id=str(cert.id),
        metadata={"patient_id": str(patient_id), "cert_type": cert.cert_type},
    )
    db.commit()
    return _serialize(cert, _user_name_map(db, _name_ids(cert)))


@router.patch("/{certification_id}/narrative", summary="Update narrative/evidence while DRAFT or PENDING_SIGNATURE")
def update_narrative(
    certification_id: uuid.UUID,
    payload: CertNarrativeUpdate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(CLINICAL_ROLES)),
):
    cert = _get_cert_or_404(db, certification_id, user)
    try:
        cert = svc.update_narrative(
            db, cert=cert,
            physician_narrative=payload.physician_narrative,
            supporting_evidence=payload.supporting_evidence,
            clinical_decline_indicators=payload.clinical_decline_indicators,
            updated_by=user.user_id, updated_by_role=user.role,
        )
    except svc.CertificationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)

    log_event(
        db=db, tenant_id=str(user.tenant_id), user_id=user.user_id, role=user.role,
        action="UPDATE_CTI_NARRATIVE", entity_type="certification", entity_id=str(cert.id),
    )
    db.commit()
    return _serialize(cert, _user_name_map(db, _name_ids(cert)))


@router.post("/{certification_id}/submit", summary="DRAFT -> PENDING_SIGNATURE, ready for physician review/signature")
def submit_for_signature(
    certification_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(CLINICAL_ROLES)),
):
    cert = _get_cert_or_404(db, certification_id, user)
    try:
        cert = svc.submit_for_signature(db, cert=cert, submitted_by=user.user_id, submitted_by_role=user.role)
    except svc.CertificationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)

    log_event(
        db=db, tenant_id=str(user.tenant_id), user_id=user.user_id, role=user.role,
        action="SUBMIT_CTI_FOR_SIGNATURE", entity_type="certification", entity_id=str(cert.id),
    )
    db.commit()
    return _serialize(cert, _user_name_map(db, _name_ids(cert)))


@router.post(
    "/{certification_id}/sign",
    summary="Physician-level signature — DRAFT/PENDING_SIGNATURE -> FINALIZED. "
    "NP/PA/RN/LVN/DPCS/Administrator are never authorized signers.",
)
def sign_certification(
    certification_id: uuid.UUID,
    db: Session = Depends(get_db),
    # allow_clinical_admin=False: administrative rank (Administrator/DPCS)
    # must never itself confer CTI signing authority. Physician-level roles
    # only — see certification_service.CTI_SIGNER_ROLES for the exact list
    # (and its defense-in-depth re-check inside sign_certification()).
    user: CurrentUser = Depends(require_roles(svc.CTI_SIGNER_ROLES, allow_clinical_admin=False)),
):
    cert = _get_cert_or_404(db, certification_id, user)
    try:
        # signed_by_role is ALWAYS the authenticated user's own role — never
        # accepted from the request body/client input.
        cert = svc.sign_certification(db, cert=cert, signed_by_user_id=user.user_id, signed_by_role=user.role)
    except svc.CertificationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)

    log_event(
        db=db, tenant_id=str(user.tenant_id), user_id=user.user_id, role=user.role,
        action="SIGN_CTI", entity_type="certification", entity_id=str(cert.id),
        metadata={"cert_type": cert.cert_type, "signed_by_role": cert.signed_by_role},
    )
    db.commit()
    return _serialize(cert, _user_name_map(db, _name_ids(cert)))


@router.post(
    "/",
    summary="[Legacy one-shot] Create-and-sign in a single call — signed_by_role is ALWAYS "
    "the authenticated user's own role, never a request-body value",
)
def finalize_cert_endpoint(
    patient_id: uuid.UUID,
    benefit_period_id: uuid.UUID,
    physician_narrative: str,
    supporting_evidence: str | None = None,
    clinical_decline_indicators: str | None = None,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles(svc.CTI_SIGNER_ROLES, allow_clinical_admin=False)),
):
    _get_patient_or_404(db, patient_id, user)
    try:
        cert = svc.create_or_finalize_cert(
            db, tenant_id=user.tenant_id, patient_id=patient_id, benefit_period_id=benefit_period_id,
            signed_by_user_id=user.user_id, signed_by_role=user.role,
            physician_narrative=physician_narrative, supporting_evidence=supporting_evidence,
            clinical_decline_indicators=clinical_decline_indicators,
        )
    except svc.CertificationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)

    log_event(
        db=db, tenant_id=str(user.tenant_id), user_id=user.user_id, role=user.role,
        action="SIGN_CTI", entity_type="certification", entity_id=str(cert.id),
        metadata={"cert_type": cert.cert_type, "signed_by_role": cert.signed_by_role},
    )
    db.commit()
    return _serialize(cert, _user_name_map(db, _name_ids(cert)))
