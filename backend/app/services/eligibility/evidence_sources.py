# app/services/eligibility/evidence_sources.py
"""
Authoritative, database-backed evidence source adapters for
ClinicalEvidenceHarvester (see clinical_evidence_harvester.py).

Each adapter maps exactly one verified persisted clinical model into
ClinicalEvidenceItem contracts with full, identifiable source-record
provenance (source_model, source_table, source_record_id). This is the
"Layer 1: database-backed authoritative evidence acquisition" referenced in
the clinical_runtime pipeline design -- distinct from the "Layer 2: legacy
compatibility extraction" implemented by LegacyEvidenceAdapter in
evidence_harvester.py, which has no database session and can therefore
never produce DOCUMENTED evidence.

Commit 2A scope: only PatientDiagnosis is implemented (diagnosis lifecycle
is fully specified and verified against the real model below). Additional
adapters (RN recertification assessment, F2F encounter/ECOG, laboratory,
other functional-assessment sources) are tracked as Commit 2B/2C follow-ups
and must not be assumed to exist by any caller of this module yet.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.clinical_runtime.contracts import (
    ClinicalEvidenceItem,
    ClinicalSourceReference,
    EvidenceOrigin,
    EvidenceStatus,
)
from app.models.patient_diagnosis import PatientDiagnosis


class SourceAdapter(ABC):
    """
    Interface for an authoritative, database-backed evidence source.

    Every adapter must:
      - filter by patient_id AND tenant_id (never trust a caller-supplied
        patient_id alone -- see DiagnosisSourceAdapter for the pattern)
      - use deterministic ordering (never rely on unordered DB iteration)
      - return ClinicalEvidenceItem instances with
        origin=EvidenceOrigin.AUTHORITATIVE_DATABASE and a source_reference
        whose source_record_id resolves to a real row this adapter read
      - never draw an eligibility/prognosis/certification/recertification/
        discharge conclusion
    """

    #: ORM model class name, reported for SOURCE_MODEL verification.
    SOURCE_MODEL: str
    #: physical table name, reported for SOURCE_TABLE verification.
    SOURCE_TABLE: str

    @abstractmethod
    def fetch(
        self,
        session: Session,
        *,
        patient_id: UUID,
        tenant_id: UUID,
        benefit_period_id: Optional[UUID] = None,
        as_of: Optional[datetime] = None,
    ) -> list[ClinicalEvidenceItem]:
        """Return evidence items for one patient, deterministically ordered."""
        raise NotImplementedError


def _diagnosis_clinical_status(diagnosis: PatientDiagnosis) -> str:
    """
    Derive a diagnosis lifecycle label without inferring ACTIVE merely
    because a row exists (per the diagnosis-evidence requirements: historical
    stroke != active stroke, resolved diagnosis != active diagnosis).

    DiagnosisStatus already carries PROPOSED/ACTIVE/REJECTED/HISTORICAL
    (app/models/enums.py); non-ACTIVE statuses are returned as-is. An
    ACTIVE-status row is only reported ACTIVE when it is also still
    `active=True` and has no resolved_date; otherwise it has been resolved
    despite its stored status not yet reflecting that and is reported
    RESOLVED.
    """

    status_value = diagnosis.status.value if hasattr(diagnosis.status, "value") else str(diagnosis.status)
    if status_value != "ACTIVE":
        return status_value
    if diagnosis.active and diagnosis.resolved_date is None:
        return "ACTIVE"
    return "RESOLVED"


class DiagnosisSourceAdapter(SourceAdapter):
    """Authoritative evidence source backed by app.models.patient_diagnosis.PatientDiagnosis."""

    SOURCE_MODEL = "PatientDiagnosis"
    SOURCE_TABLE = "patient_diagnoses"

    def fetch(
        self,
        session: Session,
        *,
        patient_id: UUID,
        tenant_id: UUID,
        benefit_period_id: Optional[UUID] = None,
        as_of: Optional[datetime] = None,
    ) -> list[ClinicalEvidenceItem]:
        query = session.query(PatientDiagnosis).filter(
            PatientDiagnosis.patient_id == patient_id,
            PatientDiagnosis.tenant_id == tenant_id,
        )
        # Deterministic ordering: effective_date, then row id (never rely on
        # unordered DB iteration -- ties on effective_date are broken by the
        # stable primary key, not insertion order).
        rows = query.order_by(
            PatientDiagnosis.effective_date.asc().nullslast(),
            PatientDiagnosis.id.asc(),
        ).all()

        items: list[ClinicalEvidenceItem] = []
        for row in rows:
            recorded_at = row.created_at
            if recorded_at is not None and recorded_at.tzinfo is None:
                recorded_at = recorded_at.replace(tzinfo=timezone.utc)

            effective_at = None
            if row.effective_date is not None:
                effective_at = datetime.combine(
                    row.effective_date, datetime.min.time(), tzinfo=timezone.utc
                )

            source_reference = ClinicalSourceReference(
                source_type="DATABASE_RECORD",
                source_id=str(row.id),
                source_record_type=self.SOURCE_TABLE,
                source_field="patient_diagnoses",
                source_recorded_at=recorded_at,
                source_author_id=str(row.created_by) if row.created_by else None,
                source_model=self.SOURCE_MODEL,
                source_table=self.SOURCE_TABLE,
            )

            items.append(
                ClinicalEvidenceItem(
                    evidence_id=f"{self.SOURCE_TABLE}:{row.id}",
                    patient_id=patient_id,
                    concept_code="DIAGNOSIS",
                    canonical_name=row.diagnosis_description,
                    status=EvidenceStatus.DOCUMENTED,
                    source_reference=source_reference,
                    benefit_period_id=benefit_period_id,
                    observed_value=row.icd10_code,
                    normalized_value={
                        "icd10_code": row.icd10_code,
                        "diagnosis_description": row.diagnosis_description,
                        "diagnosis_type": row.diagnosis_type.value
                        if hasattr(row.diagnosis_type, "value")
                        else str(row.diagnosis_type),
                        "clinical_status": _diagnosis_clinical_status(row),
                        "is_terminal": row.is_terminal,
                        "is_related_to_terminal": row.is_related_to_terminal,
                        "effective_date": row.effective_date.isoformat() if row.effective_date else None,
                        "resolved_date": row.resolved_date.isoformat() if row.resolved_date else None,
                        "effective_benefit_period_number": row.effective_benefit_period_number,
                        "resolved_benefit_period_number": row.resolved_benefit_period_number,
                    },
                    recorded_at=recorded_at,
                    effective_at=effective_at,
                    extraction_method="DIRECT_ORM_READ",
                    origin=EvidenceOrigin.AUTHORITATIVE_DATABASE,
                )
            )

        return items
