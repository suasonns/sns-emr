# services/f2f_service.py
"""
Face-to-Face (F2F) encounter service.

F2F is a separate ENCOUNTER workflow from CTI CERTIFICATION — signing/
performing authority is never combined or inferred between the two (SNS
final decision 2026-08-21). An NP who performs/signs an F2F gains ZERO
CTI certification authority.

F2F PERFORMER/SIGNER AUTHORITY (SNS final decision 2026-08-21, updated
per CMS/CDPH-aligned policy):
    - Allowed: Hospice Physician, Medical Director, Medical Director
      Designee (alias -> Medical Director), Attending Physician,
      Hospice-employed or contracted Nurse Practitioner, Hospice-employed
      or contracted Physician Assistant.
    - RN, LVN, and other disciplines may never perform/sign an F2F.
    - F2F authority does NOT grant CTI authority under any circumstance.

The F2F encounter note is SUPPORTING EVIDENCE for physician
recertification — it is never itself the certification. See
app/services/certification_service.py for CTI signing authority
(strictly independent from F2F authority).

Additive-only lifecycle: DRAFT -> FINALIZED. When an NP or PA performs the
encounter, finalization additionally requires a physician-level
attestation (Medical Director/Medical Director Designee/Attending
Physician/Hospice Physician) — never Administrator/DPCS, since
administrative rank is not clinical attestation authority.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.roles import normalize_role, role_matches
from app.models.f2f_encounter import F2FEncounter, F2FEncounterStatusEvent
from app.services.audit_logger import log_event
from app.services.recert_f2f_enforcement import (
    complete_task_with_evidence,
    validate_f2f_window,
)


class F2FError(HTTPException):
    def __init__(self, detail, status_code: int = 400):
        super().__init__(status_code=status_code, detail=detail)


# Physician-level roles that may attest a physician review of an
# NP-performed F2F. Administrator/DPCS are intentionally excluded —
# administrative rank is never clinical attestation authority.
F2F_PHYSICIAN_ATTESTOR_ROLES = ["MEDICAL_DIRECTOR", "ATTENDING_PHYSICIAN", "HOSPICE_PHYSICIAN"]

# Physician Assistant F2F authority: per updated SNS policy (CMS/CDPH
# aligned), hospice-employed or contracted PA is an authorized F2F
# performer. Kept as an explicit named flag (rather than inlining PA into
# F2F_PERFORMER_ROLES) so it stays independently auditable/toggleable if
# agency policy changes again.
F2F_PA_ENABLED = True

# Performer/signer roles for the F2F encounter itself.
F2F_PERFORMER_ROLES = list(F2F_PHYSICIAN_ATTESTOR_ROLES) + ["NP"]
if F2F_PA_ENABLED:
    F2F_PERFORMER_ROLES.append("PA")

STATUS_LABELS = {
    "DRAFT": "Draft",
    "FINALIZED": "Finalized",
}


def label_for(status: str) -> str:
    return STATUS_LABELS.get(status, status)


def is_authorized_f2f_performer(role: Optional[str]) -> bool:
    """True only for Hospice Physician / Medical Director / Medical
    Director Designee / Attending Physician / NP / PA (hospice-employed or
    contracted). RN, LVN, DPCS, and Administrator are never authorized to
    perform/sign an F2F — administrative rank and non-clinical roles are
    never encounter-performer authority."""
    return role_matches(role, F2F_PERFORMER_ROLES, allow_clinical_admin=False)


def is_authorized_f2f_physician_attestor(role: Optional[str]) -> bool:
    """True only for physician-level roles reviewing/attesting an
    NP-performed F2F. Administrator/DPCS may NEVER satisfy this gate,
    regardless of `allow_clinical_admin` fallback rules elsewhere."""
    return role_matches(role, F2F_PHYSICIAN_ATTESTOR_ROLES, allow_clinical_admin=False)


def _record_transition(
    db: Session,
    *,
    f2f: F2FEncounter,
    from_status: Optional[str],
    to_status: str,
    changed_by=None,
    changed_by_role: Optional[str] = None,
    reason: Optional[str] = None,
    automatic: bool = False,
    evidence: Optional[str] = None,
) -> F2FEncounterStatusEvent:
    now = datetime.now(timezone.utc)
    event = F2FEncounterStatusEvent(
        tenant_id=f2f.tenant_id,
        f2f_encounter_id=f2f.id,
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
        tenant_id=str(f2f.tenant_id),
        user_id=str(changed_by) if changed_by else None,
        role=changed_by_role,
        action="F2F_STATUS_TRANSITION",
        entity_type="f2f_encounter",
        entity_id=str(f2f.id),
        metadata={"from_status": from_status, "to_status": to_status, "reason": reason},
        commit=False,
    )
    return event


def get_status_history(db: Session, *, tenant_id, f2f_encounter_id) -> list[F2FEncounterStatusEvent]:
    return (
        db.query(F2FEncounterStatusEvent)
        .filter(
            F2FEncounterStatusEvent.tenant_id == tenant_id,
            F2FEncounterStatusEvent.f2f_encounter_id == f2f_encounter_id,
        )
        .order_by(F2FEncounterStatusEvent.changed_at.asc())
        .all()
    )


def list_f2f_encounters(db: Session, *, tenant_id, patient_id) -> list[F2FEncounter]:
    return (
        db.query(F2FEncounter)
        .filter(F2FEncounter.tenant_id == tenant_id, F2FEncounter.patient_id == patient_id)
        .order_by(F2FEncounter.encounter_date.desc(), F2FEncounter.created_at.desc())
        .all()
    )


def get_f2f_encounter(db: Session, *, tenant_id, f2f_encounter_id) -> Optional[F2FEncounter]:
    return (
        db.query(F2FEncounter)
        .filter(F2FEncounter.tenant_id == tenant_id, F2FEncounter.id == f2f_encounter_id)
        .first()
    )


def create_f2f(
    db: Session,
    *,
    tenant_id,
    patient_id,
    benefit_period_id,
    encounter_date,
    performed_by_role,
    performed_by_user_id=None,
    summary=None,
    created_by=None,
    created_by_role: Optional[str] = None,
):
    role = (performed_by_role or "").upper()
    if not is_authorized_f2f_performer(role):
        raise F2FError(
            f"Role '{performed_by_role}' is not authorized to perform/sign an F2F encounter. "
            f"Authorized F2F performers are: {', '.join(F2F_PERFORMER_ROLES)}.",
            status_code=403,
        )

    # Validate CMS timing window (<=30 days prior to BP start for BP3+)
    validate_f2f_window(
        db,
        benefit_period_id=benefit_period_id,
        encounter_date=encounter_date,
    )

    f2f = F2FEncounter(
        tenant_id=tenant_id,
        patient_id=patient_id,
        benefit_period_id=benefit_period_id,
        encounter_date=encounter_date,
        performed_by_role=normalize_role(role),
        performed_by_user_id=performed_by_user_id,
        summary=summary,
        status="DRAFT",
    )

    db.add(f2f)
    db.flush()

    _record_transition(
        db, f2f=f2f, from_status=None, to_status="DRAFT",
        changed_by=created_by, changed_by_role=created_by_role, reason="F2F draft created",
    )
    db.commit()
    db.refresh(f2f)
    return f2f


def finalize_f2f(
    db: Session,
    *,
    f2f: F2FEncounter,
    finalized_by=None,
    finalized_by_role: Optional[str] = None,
):
    """DRAFT -> FINALIZED. `finalized_by_role` MUST be the caller's actual
    authenticated role (the API layer must never accept this from request
    body/client input). If the encounter was performed by an NP or PA, a
    physician-level attestation (F2F_PHYSICIAN_ATTESTOR_ROLES) must already
    be recorded on the encounter (attesting_provider_user_id/attested_at)
    before this is called — see app/api/f2f.py."""
    if f2f.status == "FINALIZED":
        # Idempotent — a duplicate finalize call is returned as-is.
        return f2f

    if not is_authorized_f2f_performer(finalized_by_role) and not is_authorized_f2f_physician_attestor(
        finalized_by_role
    ):
        raise F2FError(
            f"Role '{finalized_by_role}' is not authorized to finalize an F2F encounter.",
            status_code=403,
        )

    validate_f2f_window(
        db,
        benefit_period_id=f2f.benefit_period_id,
        encounter_date=f2f.encounter_date,
    )

    from_status = f2f.status
    f2f.status = "FINALIZED"
    f2f.finalized_at = datetime.now(timezone.utc)
    db.add(f2f)
    db.flush()

    complete_task_with_evidence(
        db,
        tenant_id=f2f.tenant_id,
        patient_id=f2f.patient_id,
        benefit_period_id=f2f.benefit_period_id,
        task_type="F2F",
        ref_type="F2F_ENCOUNTER",
        ref_id=str(f2f.id),
    )

    db.commit()
    db.refresh(f2f)

    _record_transition(
        db, f2f=f2f, from_status=from_status, to_status=f2f.status,
        changed_by=finalized_by, changed_by_role=finalized_by_role,
        evidence=f"Finalized by {normalize_role(finalized_by_role)}",
    )
    db.commit()
    return f2f
