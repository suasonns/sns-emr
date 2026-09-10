"""Election / Consent Document Workflow -- readiness evaluation (Priority 6).

Business rule (per the user's explicit directive during Priority 4/5/6
planning, and consistent with docs/workflows/ReadinessDecisionMatrix.md):

    Election / Consent is documentation. It is NOT admission
    authorization, NOT SOC authorization, and NOT a benefit-period gate.
    Missing consent/election documents are AT_RISK only -- never a
    blocker, never BLOCKED, and never enforced pre-SOC or pre-admission.

Ownership / SSOT:

    The Document Registry (DocumentRecord, the same general-purpose
    document store already used for every other uploaded document in
    this system -- see app.models.document_record) is the sole owner of
    election/consent documents. This module does NOT introduce a new
    "Consent Status" or "Election Status" field/table -- per the user's
    explicit instruction, presence of a document IS the answer; a
    parallel status column would be a duplicate answer to the same
    question ("has consent been documented?") and is exactly the kind of
    SSOT violation this project has been actively removing elsewhere.

    Billing Readiness (billing_readiness_service.check_patient_billing_
    readiness) is a CONSUMER only, exactly like its consumption of
    Contracted Status / Authorization Required (Priority 5) and the
    Admission Gate. It never writes to DocumentRecord and never derives
    or caches a "consent status" of its own.

Document types (all values of DocumentRecord.document_type, an
unconstrained string column -- no migration required, consistent with
how "AUTHORIZATION"/"ELIGIBILITY_SUBMISSION" are already used from the
facesheet UI's existing DocumentUploadWidget):

    ELECTION_STATEMENT
    CONSENT_FORM
    PATIENT_RIGHTS
    HIPAA_ACKNOWLEDGEMENT
    NOTICE_OF_PRIVACY_PRACTICES
    ADVANCE_DIRECTIVE
    FINANCIAL_RESPONSIBILITY
    OTHER_ADMISSION_DOCUMENT

Any ACTIVE document of ANY of these types counts as "election/consent
documentation is present" -- staff are not required to upload every
type; different agencies collect different subsets of this packet
(some fax it, some scan it later, some receive it electronically), and
the whole point of this priority is that SOC/admission is never blocked
waiting on this paperwork.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.models.document_record import DocumentRecord

ELECTION_CONSENT_DOCUMENT_TYPES = {
    "ELECTION_STATEMENT",
    "CONSENT_FORM",
    "PATIENT_RIGHTS",
    "HIPAA_ACKNOWLEDGEMENT",
    "NOTICE_OF_PRIVACY_PRACTICES",
    "ADVANCE_DIRECTIVE",
    "FINANCIAL_RESPONSIBILITY",
    "OTHER_ADMISSION_DOCUMENT",
}

_MISSING_CONSENT_WARNING = (
    "Election/consent documentation (election statement, consent form, "
    "patient rights, HIPAA acknowledgement, notice of privacy practices, "
    "advance directive, or financial responsibility form) has not been "
    "uploaded yet. This does not block admission, SOC, or billing "
    "readiness -- follow up to obtain and upload the signed packet."
)


@dataclass(frozen=True)
class ReadinessFinding:
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def has_election_consent_evidence(
    db: Session, *, tenant_id: str, patient_id: str
) -> bool:
    return (
        db.query(DocumentRecord.id)
        .filter(
            DocumentRecord.tenant_id == tenant_id,
            DocumentRecord.patient_id == patient_id,
            DocumentRecord.document_type.in_(ELECTION_CONSENT_DOCUMENT_TYPES),
            DocumentRecord.lifecycle_status == "ACTIVE",
        )
        .first()
        is not None
    )


def evaluate_election_consent_readiness(
    db: Session, *, tenant_id: str, patient_id: str
) -> ReadinessFinding:
    """
    AT_RISK-only evaluation -- never returns a blocker. Called only from
    the post-admission billing-readiness path (i.e. once a benefit period
    already exists for the patient), matching the business rule that this
    is a post-admission compliance check, not an admission gate.
    """
    if has_election_consent_evidence(db, tenant_id=tenant_id, patient_id=patient_id):
        return ReadinessFinding()
    return ReadinessFinding(warnings=[_MISSING_CONSENT_WARNING])
