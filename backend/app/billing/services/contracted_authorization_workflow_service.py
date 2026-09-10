"""Contracted Status Workflow + Authorization Workflow -- readiness
evaluation (Priority 5).

Per docs/workflows/ReadinessDecisionMatrix.md and
docs/workflows/AuthorizationWorkflow.md: these two business concepts each
have exactly one owner --

  - Contracted Status Workflow owns `PatientFaceSheet.contracted_status`
    and any contracted-review evidence.
  - Authorization Workflow owns `PatientFaceSheet.authorization_required_status`
    and authorization evidence (`EligibilitySourceDocument` rows classified
    AUTHORIZATION_DOCUMENT / NON_AUTH_VERIFICATION).

Billing Readiness (`billing_readiness_service.check_patient_billing_
readiness`) is a CONSUMER of both -- it calls the two evaluate_* functions
below exactly the way it already calls `evaluate_admission_gate` and
`resolve_payer_sequence`, and folds the returned blockers/warnings into
its own list. Readiness never re-implements this business logic inline
and never writes to either field.

Severity per docs/workflows/ReadinessDecisionMatrix.md (final):

  Contracted Status:
    YES     -> no finding
    NO      -> warning (AT_RISK) -- agency policy question, not hard-coded
               BLOCKED without confirmation
    UNKNOWN -> warning (AT_RISK) -- incomplete staff review

  Authorization Required:
    UNKNOWN               -> warning (AT_RISK)
    YES, evidence present  -> no finding
    YES, no evidence       -> blocker (BLOCKED-tier)
    NO,  evidence present  -> no finding
    NO,  no evidence       -> warning (AT_RISK), not a blocker

"Evidence present" reuses the existing `EligibilitySourceDocument`
classifications rather than introducing new duplicate types (SSOT: one
document taxonomy, not a second one per workflow) --
AUTHORIZATION_DOCUMENT for Authorization Required = YES,
NON_AUTH_VERIFICATION for Authorization Required = NO.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.billing.models.eligibility_source_document import EligibilitySourceDocument

CONTRACTED_STATUS_VALUES = {"YES", "NO", "UNKNOWN"}
AUTHORIZATION_REQUIRED_STATUS_VALUES = {"YES", "NO", "UNKNOWN"}

CONTRACTED_STATUS_LABELS = {
    "YES": "Contracted",
    "NO": "Not Contracted",
    "UNKNOWN": "Unknown",
    None: "Unknown",
}

AUTHORIZATION_REQUIRED_STATUS_LABELS = {
    "YES": "Authorization Required",
    "NO": "Authorization Not Required",
    "UNKNOWN": "Unknown",
    None: "Unknown",
}

_AUTHORIZATION_EVIDENCE_TYPE = "AUTHORIZATION_DOCUMENT"
_NON_AUTH_EVIDENCE_TYPE = "NON_AUTH_VERIFICATION"


@dataclass(frozen=True)
class ReadinessFinding:
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def contracted_status_label(contracted_status: str | None) -> str:
    return CONTRACTED_STATUS_LABELS.get(contracted_status, "Unknown")


def authorization_required_status_label(authorization_required_status: str | None) -> str:
    return AUTHORIZATION_REQUIRED_STATUS_LABELS.get(authorization_required_status, "Unknown")


def evaluate_contracted_status_readiness(
    *, contracted_status: str | None
) -> ReadinessFinding:
    """
    Pure evaluation -- no DB access needed. Contracted Status Workflow is
    the only owner of `contracted_status`; this function only reads the
    already-staff-entered value.
    """
    if contracted_status == "YES":
        return ReadinessFinding()
    if contracted_status == "NO":
        return ReadinessFinding(
            warnings=[
                "Agency is not contracted with the confirmed payer -- "
                "billing policy review recommended before claim submission."
            ]
        )
    # None or "UNKNOWN"
    return ReadinessFinding(
        warnings=["Contracted status has not been reviewed (Unknown)."]
    )


def _has_active_evidence(
    db: Session, *, tenant_id: str, patient_id: str, document_type: str
) -> bool:
    return (
        db.query(EligibilitySourceDocument.id)
        .filter(
            EligibilitySourceDocument.tenant_id == tenant_id,
            EligibilitySourceDocument.patient_id == patient_id,
            EligibilitySourceDocument.document_type == document_type,
            EligibilitySourceDocument.status == "ACTIVE",
        )
        .first()
        is not None
    )


def evaluate_authorization_readiness(
    db: Session,
    *,
    tenant_id: str,
    patient_id: str,
    authorization_required_status: str | None,
) -> ReadinessFinding:
    """
    Authorization Workflow is the only owner of
    `authorization_required_status` and its evidence documents. This
    function only reads those already-staff-entered/uploaded values.
    """
    if authorization_required_status == "YES":
        if _has_active_evidence(
            db,
            tenant_id=tenant_id,
            patient_id=patient_id,
            document_type=_AUTHORIZATION_EVIDENCE_TYPE,
        ):
            return ReadinessFinding()
        return ReadinessFinding(
            blockers=[
                "Authorization Required = YES but no authorization evidence "
                "is on file -- claim cannot be safely submitted."
            ]
        )

    if authorization_required_status == "NO":
        if _has_active_evidence(
            db,
            tenant_id=tenant_id,
            patient_id=patient_id,
            document_type=_NON_AUTH_EVIDENCE_TYPE,
        ):
            return ReadinessFinding()
        return ReadinessFinding(
            warnings=[
                "Authorization Required = NO but no non-authorization "
                "verification evidence is on file -- review recommended."
            ]
        )

    # None or "UNKNOWN"
    return ReadinessFinding(
        warnings=["Authorization requirement has not been reviewed (Unknown)."]
    )
