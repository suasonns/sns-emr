# services/certification_service.py
"""
Certification of Terminal Illness (CTI) / Recertification service.

Phase 1 lifecycle expansion (owner directive 2026-08-21, additive only):

    DRAFT -> PENDING_SIGNATURE -> FINALIZED -> [SUPERSEDED by next cert]

DRAFT captures the physician narrative + supporting clinical/LCD evidence
required by CMS before a certifying physician signs (CMS eligibility and
terminal-prognosis support must be documented using patient-specific
evidence — clinical decline, functional status, comorbidities,
disease-specific indicators — not conclusions alone). PENDING_SIGNATURE is
the reviewable state once a narrative is attached; FINALIZED is the signed,
legally-binding record. Any pre-existing "FINALIZED" cert with no draft
history remains fully valid — this expansion does not alter or require
touching prior records.

CTI SIGNING AUTHORITY (SNS final decision 2026-08-21) — CTI is a physician
CERTIFICATION workflow, strictly separate from the F2F ENCOUNTER workflow:
    - Allowed: Attending Physician, Medical Director, Medical Director
      Designee (alias -> Medical Director), Hospice Physician.
    - NOT allowed: Nurse Practitioner, Physician Assistant, RN, LVN, DPCS,
      Administrator — for INITIAL and RECERT alike.
    - A provider's ability to perform/sign a Face-to-Face encounter (NP,
      when hospice-employed) NEVER implies CTI certification authority —
      the two workflows/authorities are never combined or inferred from
      one another. See app/services/f2f_service.py for F2F authority.

`signed_by_role` is ALWAYS derived from the actual authenticated user's
role (never a client-supplied request value) — the prior implementation
accepted `signed_by_role` as a plain request field, meaning an
Administrator account could self-declare "MD" and finalize a certification
despite holding no prescribing/certifying authority. This mirrors the same
authority-separation fix already applied to Physician Orders.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.roles import normalize_role, role_matches
from app.models.benefit_period import BenefitPeriod
from app.models.certification import Certification, CertificationStatusEvent
from app.services.audit_logger import log_event
from app.services.evidence.harvest_service import harvest_from_source
from app.services.recert_f2f_enforcement import (
    bp_index_date_derived,
    complete_task_with_evidence,
    require_f2f_completed_for_bp3_plus,
)

logger = logging.getLogger("sns_emr")


class CertificationError(HTTPException):
    def __init__(self, detail: str, status_code: int = 400):
        super().__init__(status_code=status_code, detail=detail)


# Physician-level roles ONLY. MEDICAL_DIRECTOR_DESIGNEE normalizes to
# MEDICAL_DIRECTOR via app.core.roles._ALIASES. NP, PA, RN, LVN, DPCS, and
# Administrator are intentionally excluded — they are not authorized CTI
# signers per SNS policy, for both INITIAL and RECERT.
CTI_SIGNER_ROLES = ["MEDICAL_DIRECTOR", "ATTENDING_PHYSICIAN", "HOSPICE_PHYSICIAN"]

STATUS_LABELS = {
    "DRAFT": "Draft",
    "PENDING_SIGNATURE": "CTI Pending Signature",
    "FINALIZED": "Signed",
    "SUPERSEDED": "Superseded",
}


def label_for(status: str) -> str:
    return STATUS_LABELS.get(status, status)


def is_authorized_cti_signer(role: Optional[str]) -> bool:
    """True only for physician-level roles. NP/PA/RN/LVN/DPCS/Administrator
    are never authorized to sign a CTI, regardless of `allow_clinical_admin`
    fallback rules elsewhere in the system."""
    return role_matches(role, CTI_SIGNER_ROLES, allow_clinical_admin=False)


def _record_transition(
    db: Session,
    *,
    cert: Certification,
    from_status: Optional[str],
    to_status: str,
    changed_by=None,
    changed_by_role: Optional[str] = None,
    reason: Optional[str] = None,
    automatic: bool = False,
    evidence: Optional[str] = None,
) -> CertificationStatusEvent:
    now = datetime.now(timezone.utc)
    event = CertificationStatusEvent(
        tenant_id=cert.tenant_id,
        certification_id=cert.id,
        from_status=from_status,
        to_status=to_status,
        changed_by_user_id=changed_by,
        changed_by_role=changed_by_role,
        changed_at=now,
        reason=reason,
        automatic=automatic,
        evidence=evidence,
    )
    db.add(event)
    db.flush()

    log_event(
        db=db,
        tenant_id=str(cert.tenant_id),
        user_id=str(changed_by) if changed_by else None,
        role=changed_by_role,
        action="CERTIFICATION_STATUS_TRANSITION",
        entity_type="certification",
        entity_id=str(cert.id),
        metadata={"from_status": from_status, "to_status": to_status, "reason": reason},
        commit=False,
    )
    return event


def get_status_history(db: Session, *, tenant_id, certification_id) -> list[CertificationStatusEvent]:
    return (
        db.query(CertificationStatusEvent)
        .filter(
            CertificationStatusEvent.tenant_id == tenant_id,
            CertificationStatusEvent.certification_id == certification_id,
        )
        .order_by(CertificationStatusEvent.changed_at.asc())
        .all()
    )


def list_certifications(db: Session, *, tenant_id, patient_id) -> list[Certification]:
    return (
        db.query(Certification)
        .filter(Certification.tenant_id == tenant_id, Certification.patient_id == patient_id)
        .order_by(Certification.created_at.desc())
        .all()
    )


def get_certification(db: Session, *, tenant_id, certification_id) -> Optional[Certification]:
    return (
        db.query(Certification)
        .filter(Certification.tenant_id == tenant_id, Certification.id == certification_id)
        .first()
    )


def _resolve_bp_and_type(db: Session, *, tenant_id, patient_id, benefit_period_id):
    bp = (
        db.query(BenefitPeriod)
        .filter(BenefitPeriod.id == benefit_period_id, BenefitPeriod.tenant_id == tenant_id)
        .first()
    )
    if not bp:
        raise CertificationError("Benefit period not found", status_code=404)
    if str(bp.patient_id) != str(patient_id):
        raise CertificationError("Benefit period does not belong to the specified patient.")

    idx = bp_index_date_derived(db, patient_id=patient_id, tenant_id=tenant_id, benefit_period_id=benefit_period_id)
    cert_type = "INITIAL" if idx == 1 else "RECERT"
    return bp, idx, cert_type


def create_draft(
    db: Session,
    *,
    tenant_id,
    patient_id,
    benefit_period_id,
    physician_narrative: str,
    supporting_evidence: Optional[str] = None,
    clinical_decline_indicators: Optional[str] = None,
    created_by=None,
    created_by_role: Optional[str] = None,
) -> Certification:
    """Create a DRAFT certification capturing the physician narrative and
    supporting clinical/LCD evidence required before signature. Any
    clinical role may prepare the draft (e.g. RN/case manager assembling
    supporting documentation for physician review) — only the signing step
    is restricted to CTI_SIGNER_ROLES."""
    bp, idx, cert_type = _resolve_bp_and_type(
        db, tenant_id=tenant_id, patient_id=patient_id, benefit_period_id=benefit_period_id
    )

    if not physician_narrative or not physician_narrative.strip():
        raise CertificationError(
            "physician_narrative is required — CMS requires patient-specific evidence "
            "(clinical decline, functional status, comorbidities, disease-specific "
            "indicators) supporting a prognosis of six months or less, not conclusions alone."
        )

    existing = (
        db.query(Certification)
        .filter(
            Certification.tenant_id == tenant_id,
            Certification.patient_id == patient_id,
            Certification.benefit_period_id == benefit_period_id,
            Certification.status.in_(["DRAFT", "PENDING_SIGNATURE", "FINALIZED"]),
        )
        .first()
    )
    if existing:
        return existing

    now = datetime.now(timezone.utc)
    cert = Certification(
        tenant_id=tenant_id,
        patient_id=patient_id,
        benefit_period_id=benefit_period_id,
        cert_type=cert_type,
        signed_at=now,  # placeholder until finalized; overwritten by sign_certification()
        effective_date=bp.start_date,
        signed_by_role="",
        status="DRAFT",
        physician_narrative=physician_narrative.strip(),
        supporting_evidence=(supporting_evidence or "").strip() or None,
        clinical_decline_indicators=(clinical_decline_indicators or "").strip() or None,
        narrative_by=created_by,
        narrative_at=now,
        created_by=created_by,
    )
    db.add(cert)
    db.flush()

    _record_transition(
        db, cert=cert, from_status=None, to_status="DRAFT",
        changed_by=created_by, changed_by_role=created_by_role, reason="CTI draft created",
    )
    db.commit()
    db.refresh(cert)
    return cert


def submit_for_signature(
    db: Session, *, cert: Certification, submitted_by=None, submitted_by_role: Optional[str] = None,
) -> Certification:
    """DRAFT -> PENDING_SIGNATURE, once narrative/evidence are ready for
    physician review and signature."""
    if cert.status != "DRAFT":
        raise CertificationError(f"Only DRAFT certifications can be submitted for signature (current: {cert.status})")
    if not cert.physician_narrative:
        raise CertificationError("physician_narrative is required before submitting for signature")

    from_status = cert.status
    cert.status = "PENDING_SIGNATURE"
    db.add(cert)
    db.commit()
    db.refresh(cert)

    _record_transition(
        db, cert=cert, from_status=from_status, to_status=cert.status,
        changed_by=submitted_by, changed_by_role=submitted_by_role,
    )
    db.commit()
    return cert


def update_narrative(
    db: Session,
    *,
    cert: Certification,
    physician_narrative: Optional[str] = None,
    supporting_evidence: Optional[str] = None,
    clinical_decline_indicators: Optional[str] = None,
    updated_by=None,
    updated_by_role: Optional[str] = None,
) -> Certification:
    """Update narrative/evidence while still DRAFT or PENDING_SIGNATURE
    (before the record is legally finalized)."""
    if cert.status not in ("DRAFT", "PENDING_SIGNATURE"):
        raise CertificationError(f"Cannot edit narrative once status is {cert.status}")

    if physician_narrative is not None:
        cert.physician_narrative = physician_narrative.strip()
    if supporting_evidence is not None:
        cert.supporting_evidence = supporting_evidence.strip() or None
    if clinical_decline_indicators is not None:
        cert.clinical_decline_indicators = clinical_decline_indicators.strip() or None
    cert.narrative_by = updated_by or cert.narrative_by
    cert.narrative_at = datetime.now(timezone.utc)
    db.add(cert)
    db.commit()
    db.refresh(cert)
    return cert


def sign_certification(
    db: Session,
    *,
    cert: Certification,
    signed_by_user_id,
    signed_by_role: str,
) -> Certification:
    """DRAFT/PENDING_SIGNATURE -> FINALIZED. `signed_by_role` MUST be the
    caller's actual authenticated role (the API layer must never accept
    this from request body/client input) and MUST be a CTI_SIGNER_ROLES
    role — physician-level only; NP/PA/RN/LVN/DPCS/Administrator are
    rejected here even if the endpoint's coarse-grained gate were
    misconfigured, as defense in depth."""
    if cert.status not in ("DRAFT", "PENDING_SIGNATURE", "FINALIZED"):
        raise CertificationError(f"Cannot sign a certification with status {cert.status}")
    if cert.status == "FINALIZED":
        # Idempotent — a cert already finalized (e.g. legacy pre-Phase-1
        # record, or a duplicate signing call) is returned as-is.
        return cert
    if not cert.physician_narrative:
        raise CertificationError("physician_narrative is required before signature")

    if not is_authorized_cti_signer(signed_by_role):
        raise CertificationError(
            f"Role '{signed_by_role}' is not authorized to sign a CTI. "
            f"CTI signing authority is limited to: {', '.join(CTI_SIGNER_ROLES)}. "
            f"Nurse Practitioners, Physician Assistants, RN, LVN, DPCS, and "
            f"Administrator may never sign a CTI.",
            status_code=403,
        )

    bp = db.query(BenefitPeriod).filter(BenefitPeriod.id == cert.benefit_period_id).first()
    if not bp:
        raise CertificationError("Benefit period not found", status_code=404)

    if bp_index_date_derived(
        db, patient_id=cert.patient_id, tenant_id=cert.tenant_id, benefit_period_id=cert.benefit_period_id,
    ) >= 3:
        require_f2f_completed_for_bp3_plus(
            db, patient_id=cert.patient_id, tenant_id=cert.tenant_id, benefit_period_id=cert.benefit_period_id,
        )

    now = datetime.now(timezone.utc)
    earliest_allowed = datetime.combine(bp.start_date - timedelta(days=15), datetime.min.time(), tzinfo=timezone.utc)
    if now < earliest_allowed:
        raise CertificationError(
            "Certification/recertification cannot be signed more than 15 days before period start."
        )

    from_status = cert.status
    cert.status = "FINALIZED"
    cert.signed_at = now
    cert.signed_by_user_id = signed_by_user_id
    cert.signed_by_role = normalize_role(signed_by_role)
    cert.expires_at = datetime.combine(bp.end_date, datetime.min.time(), tzinfo=timezone.utc) if bp.end_date else None
    db.add(cert)
    db.flush()

    task_type = "CERTIFICATION" if cert.cert_type == "INITIAL" else "RECERTIFICATION"
    complete_task_with_evidence(
        db, tenant_id=cert.tenant_id, patient_id=cert.patient_id, benefit_period_id=cert.benefit_period_id,
        task_type=task_type, ref_type=task_type, ref_id=str(cert.id),
    )

    # Chain: mark the immediately-prior finalized cert for this patient as
    # superseded by this one.
    prior = (
        db.query(Certification)
        .filter(
            Certification.tenant_id == cert.tenant_id,
            Certification.patient_id == cert.patient_id,
            Certification.status == "FINALIZED",
            Certification.id != cert.id,
        )
        .order_by(Certification.signed_at.desc())
        .first()
    )
    if prior and not prior.superseded_by_id:
        prior.superseded_by_id = cert.id
        prior.superseded_at = now
        db.add(prior)

    db.commit()
    db.refresh(cert)

    _record_transition(
        db, cert=cert, from_status=from_status, to_status=cert.status,
        changed_by=signed_by_user_id, changed_by_role=cert.signed_by_role,
        evidence=f"Signed by {cert.signed_by_role}",
    )
    db.commit()

    # ------------------------------
    # AI EVIDENCE HARVESTER (safe, isolated -- see harvest_service
    # docstring). Called standalone AFTER our own commits above, so a
    # harvesting failure can never affect CTI signing.
    # ------------------------------
    try:
        narrative_text = "\n".join(
            filter(
                None,
                [
                    (cert.physician_narrative or "").strip(),
                    (cert.supporting_evidence or "").strip(),
                    (cert.clinical_decline_indicators or "").strip(),
                ],
            )
        )
        harvest_from_source(
            db=db,
            tenant_id=cert.tenant_id,
            patient_id=cert.patient_id,
            source_type="CERTIFICATION",
            source_record_id=cert.id,
            recorded_at=cert.signed_at,
            text=narrative_text,
            discipline="MD",
            recorded_by_user_id=cert.signed_by_user_id,
        )
    except Exception:
        logger.exception(
            "Failed to harvest certification into AI evidence registry",
            extra={"certification_id": str(cert.id)},
        )

    return cert


def create_or_finalize_cert(
    db: Session,
    *,
    tenant_id,
    patient_id,
    benefit_period_id,
    signed_by_user_id,
    signed_by_role: str,
    physician_narrative: str,
    supporting_evidence: Optional[str] = None,
    clinical_decline_indicators: Optional[str] = None,
):
    """Convenience one-shot path: create the DRAFT (if none exists yet) and
    immediately sign it. `signed_by_role` MUST be the caller's actual
    authenticated role, resolved server-side — never accepted from request
    body. Kept for callers that don't need the separate draft/review step."""
    existing = (
        db.query(Certification)
        .filter(
            Certification.tenant_id == tenant_id,
            Certification.patient_id == patient_id,
            Certification.benefit_period_id == benefit_period_id,
            Certification.status == "FINALIZED",
        )
        .first()
    )
    if existing:
        return existing

    cert = create_draft(
        db, tenant_id=tenant_id, patient_id=patient_id, benefit_period_id=benefit_period_id,
        physician_narrative=physician_narrative, supporting_evidence=supporting_evidence,
        clinical_decline_indicators=clinical_decline_indicators,
        created_by=signed_by_user_id, created_by_role=signed_by_role,
    )
    return sign_certification(db, cert=cert, signed_by_user_id=signed_by_user_id, signed_by_role=signed_by_role)
