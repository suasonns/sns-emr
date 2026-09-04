# app/services/eligibility/clinical_evidence_harvester.py
"""
Authoritative, database-backed ClinicalEvidenceHarvester (Commit 2 of the
clinical_runtime pipeline -- see app/domain/clinical_runtime/contracts.py).

This is Layer 1 (database-backed authoritative evidence acquisition). Layer
2 (legacy compatibility extraction) is LegacyEvidenceAdapter in
evidence_harvester.py -- its output is a supplementary, clearly-labeled
(EvidenceOrigin.LEGACY_ADAPTER) bundle merged in only when requested, never
a substitute for Layer 1, and never DOCUMENTED.

Commit 2A scope: only the diagnosis source adapter is wired in. Commit 2B
adds the RN recertification assessment and Certification source adapters.
Commit 2C adds F2FEncounter (functional assessment / ECOG). Commit 2D adds
structured cross-source conflict detection (ClinicalEvidenceBundle.conflicts)
and missing-workflow-requirement detection
(ClinicalEvidenceBundle.missing_requirements), and replaces the prior
UUID-influenced final ordering with an explicit clinical-chronology order.
Laboratory and other additional sources remain follow-ups.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.clinical_runtime.contracts import (
    ClinicalEvidenceBundle,
    EvidenceErrorCode,
)
from app.models.patient import Patient
from app.services.eligibility.evidence_conflict_detection import (
    detect_functional_score_conflicts,
    detect_missing_rn_recert_requirement,
)
from app.services.eligibility.evidence_sources import (
    CertificationSourceAdapter,
    DiagnosisSourceAdapter,
    F2FEncounterSourceAdapter,
    RNRecertAssessmentSourceAdapter,
    SourceAdapter,
)


@dataclass(frozen=True)
class ActorContext:
    """
    Authenticated-request actor context. Required whenever harvesting is
    initiated through an authenticated application request (not required for
    trusted internal/background callers that already hold a verified
    session, e.g. a batch job running under its own service identity).

    Caller-supplied context may constrain the query (e.g. tenant_id used to
    scope the lookup); it never replaces source-record identity -- every
    evidence item's provenance still comes from the row the adapter read,
    not from this context.
    """

    tenant_id: UUID
    actor_user_id: Optional[UUID] = None


class PatientNotFoundError(ValueError):
    """Raised when patient_id does not resolve to a persisted Patient row."""


class CrossTenantAccessError(PermissionError):
    """
    Raised when the resolved patient's tenant_id does not match the
    tenant_id supplied via actor_context or the tenant_id argument.
    Never silently scoped away -- this is a security boundary violation and
    must fail loudly.
    """


class ClinicalEvidenceHarvester:
    """
    harvest(session, patient_id, tenant_id, ...) -> ClinicalEvidenceBundle

    Queries authoritative, persisted clinical records through explicit
    source adapters (never through the legacy harvest_clinical_facts() duck-
    typed path). Enforces patient/tenant isolation before running any
    adapter.
    """

    def __init__(self, adapters: Optional[list[SourceAdapter]] = None):
        # Commit 2A: diagnosis only. Commit 2B adds RN recertification
        # assessment and Certification (CTI/recert) sources. Commit 2C adds
        # F2FEncounter (dedicated functional-assessment/ECOG source).
        # Additional adapters (negative/conflicting evidence) are appended
        # in follow-up commits (2D) -- see evidence_sources.py.
        self._adapters: list[SourceAdapter] = adapters if adapters is not None else [
            DiagnosisSourceAdapter(),
            RNRecertAssessmentSourceAdapter(),
            CertificationSourceAdapter(),
            F2FEncounterSourceAdapter(),
        ]

    def harvest(
        self,
        session: Session,
        *,
        patient_id: UUID,
        tenant_id: UUID,
        encounter_id: Optional[str] = None,
        benefit_period_id: Optional[UUID] = None,
        as_of: Optional[datetime] = None,
        actor_context: Optional[ActorContext] = None,
    ) -> ClinicalEvidenceBundle:
        if actor_context is not None and actor_context.tenant_id != tenant_id:
            raise CrossTenantAccessError(
                f"actor_context.tenant_id={actor_context.tenant_id} does not match "
                f"requested tenant_id={tenant_id}"
            )

        patient = (
            session.query(Patient)
            .filter(Patient.id == patient_id, Patient.tenant_id == tenant_id)
            .one_or_none()
        )
        if patient is None:
            # Deliberately does not distinguish "patient does not exist" from
            # "patient exists in a different tenant" in the exception message
            # -- either way the caller gets nothing, so cross-tenant existence
            # is never leaked.
            raise PatientNotFoundError(
                f"No patient found for patient_id={patient_id} in tenant_id={tenant_id}"
            )

        generated_at = datetime.now(timezone.utc)
        items = []
        warnings: list[str] = []
        errors: list[EvidenceErrorCode] = []

        for adapter in self._adapters:
            try:
                items.extend(
                    adapter.fetch(
                        session,
                        patient_id=patient_id,
                        tenant_id=tenant_id,
                        benefit_period_id=benefit_period_id,
                        as_of=as_of,
                    )
                )
            except Exception as exc:  # noqa: BLE001 - convert to a typed bundle error, never raise past this boundary
                errors.append(EvidenceErrorCode.EVIDENCE_SOURCE_UNAVAILABLE)
                warnings.append(f"{adapter.SOURCE_MODEL} adapter failed: {exc.__class__.__name__}")

        # Canonical clinical-chronology ordering across adapters:
        # effective_at asc (nulls last), recorded_at asc (nulls last),
        # source_model, source_record_id, source_field, evidence_id.
        # evidence_id is only a final, purely-for-determinism tie-break --
        # it is a hash-derived string and MUST NOT be treated as clinical
        # chronology (a prior bug: the previous (concept_code, evidence_id)
        # sort let UUID lexical order silently override real timestamps
        # whenever two items shared a concept_code).
        _min = datetime.min.replace(tzinfo=timezone.utc)

        def _order_key(item):
            ref = item.source_reference
            return (
                item.effective_at is None,
                item.effective_at or _min,
                item.recorded_at is None,
                item.recorded_at or _min,
                ref.source_model or "",
                ref.source_id or "",
                ref.source_field or "",
                item.evidence_id,
            )

        items.sort(key=_order_key)

        conflicts = detect_functional_score_conflicts(items, now=generated_at)
        missing_requirements = detect_missing_rn_recert_requirement(
            items,
            patient_id=patient_id,
            benefit_period_id=benefit_period_id,
            now=generated_at,
        )

        return ClinicalEvidenceBundle(
            patient_id=patient_id,
            items=items,
            conflicts=conflicts,
            missing_requirements=missing_requirements,
            encounter_id=encounter_id,
            benefit_period_id=benefit_period_id,
            generated_at=generated_at,
            warnings=warnings,
            errors=errors,
        )
