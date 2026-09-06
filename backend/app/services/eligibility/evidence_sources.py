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

Commit 2A scope: PatientDiagnosis. Commit 2B adds RN recertification
assessment (RNRecertAssessment) and Certification (CTI/recert)
source-adapters. Commit 2C adds F2FEncounter (the dedicated face-to-face
functional-assessment source, including ECOG which RNRecertAssessment does
not carry). All are verified against their real models below. Additional
adapters (laboratory, other negative/conflicting evidence) are tracked as
Commit 2D follow-ups and must not be assumed to exist by any caller of this
module yet.
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
from app.models.rn_recert_assessment import RNRecertAssessment
from app.models.certification import Certification
from app.models.f2f_encounter import F2FEncounter


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
                source_record_type="DIAGNOSIS_RECORD",
                source_field="icd10_code",
                source_recorded_at=recorded_at,
                source_effective_at=effective_at,
                source_author_id=str(row.created_by) if row.created_by else None,
                source_model=self.SOURCE_MODEL,
                source_table=self.SOURCE_TABLE,
                source_patient_id=row.patient_id,
                # PatientDiagnosis has no encounter or BenefitPeriod foreign
                # key -- only an integer effective_benefit_period_number
                # (see normalized_value below). Left None rather than
                # fabricated from the caller's request parameter.
                source_encounter_id=None,
                source_benefit_period_id=None,
            )

            items.append(
                ClinicalEvidenceItem(
                    evidence_id=f"{self.SOURCE_TABLE}:{row.id}",
                    patient_id=patient_id,
                    concept_code="DIAGNOSIS",
                    canonical_name=row.diagnosis_description,
                    status=EvidenceStatus.DOCUMENTED,
                    source_reference=source_reference,
                    # Not set from the caller's benefit_period_id parameter:
                    # PatientDiagnosis carries no BenefitPeriod foreign key,
                    # only the integer effective_benefit_period_number
                    # captured in normalized_value below. A real
                    # benefit-period association must not be fabricated from
                    # a pass-through parameter.
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


def _tz_aware(value):
    """Attach UTC if a naive datetime is read from the database (Postgres
    `TIMESTAMP WITHOUT TIME ZONE` columns come back naive from psycopg2 even
    though the application always writes/interprets them as UTC)."""
    if value is not None and value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


class RNRecertAssessmentSourceAdapter(SourceAdapter):
    """
    Authoritative evidence source backed by
    app.models.rn_recert_assessment.RNRecertAssessment -- the RN's structured
    recertification assessment (PPS/KPS/FAST/NYHA, ADL level, primary
    diagnosis, narrative translation output).

    Deliberately excludes `eligibility_recommendation` from the surfaced
    evidence: that field is the RN's own working recommendation, not a
    verified clinical fact, and this adapter must never surface (let alone
    generate) an eligibility conclusion.

    RNRecertAssessment has no encounter/Visit foreign key (Visit carries only
    admission_id, no benefit_period_id) -- the assessment record itself IS
    the recertification encounter; source_encounter_id is left None rather
    than fabricated.
    """

    SOURCE_MODEL = "RNRecertAssessment"
    SOURCE_TABLE = "rn_recert_assessments"

    def fetch(
        self,
        session: Session,
        *,
        patient_id: UUID,
        tenant_id: UUID,
        benefit_period_id: Optional[UUID] = None,
        as_of: Optional[datetime] = None,
    ) -> list[ClinicalEvidenceItem]:
        query = session.query(RNRecertAssessment).filter(
            RNRecertAssessment.patient_id == patient_id,
            # tenant_id is nullable on this model (defense-in-depth column,
            # not always populated by every caller). patient_id is already
            # tenant-verified by ClinicalEvidenceHarvester.harvest() before
            # any adapter runs, so a NULL tenant_id row for this exact
            # patient is not a cross-tenant leak; a row explicitly stamped
            # with a DIFFERENT tenant_id is still excluded.
            (RNRecertAssessment.tenant_id.is_(None)) | (RNRecertAssessment.tenant_id == tenant_id),
        )
        if benefit_period_id is not None:
            query = query.filter(RNRecertAssessment.benefit_period_id == benefit_period_id)

        rows = query.order_by(
            RNRecertAssessment.created_at.asc(),
            RNRecertAssessment.id.asc(),
        ).all()

        items: list[ClinicalEvidenceItem] = []
        for row in rows:
            recorded_at = _tz_aware(row.created_at)
            effective_at = _tz_aware(row.attested_at) or _tz_aware(row.finalized_at)

            if as_of is not None and effective_at is not None and effective_at > as_of:
                # Future-effective exclusion: an assessment attested/
                # finalized after the as-of point must not be treated as
                # evidence available "as of" that earlier moment.
                continue

            author_id = row.attesting_provider_user_id or row.created_by_user_id

            source_reference = ClinicalSourceReference(
                source_type="DATABASE_RECORD",
                source_id=str(row.id),
                source_record_type="RN_RECERT_ASSESSMENT",
                source_field="normalized_observations_json",
                source_recorded_at=recorded_at,
                source_effective_at=effective_at,
                source_author_id=str(author_id) if author_id else None,
                authentication_status="ATTESTED" if row.attested_at is not None else "UNATTESTED",
                source_model=self.SOURCE_MODEL,
                source_table=self.SOURCE_TABLE,
                source_patient_id=row.patient_id,
                source_encounter_id=None,
                source_benefit_period_id=row.benefit_period_id,
            )

            items.append(
                ClinicalEvidenceItem(
                    evidence_id=f"{self.SOURCE_TABLE}:{row.id}",
                    patient_id=patient_id,
                    concept_code="RN_RECERT_ASSESSMENT",
                    canonical_name="RN Recertification Assessment",
                    status=EvidenceStatus.DOCUMENTED,
                    source_reference=source_reference,
                    encounter_id=None,
                    benefit_period_id=row.benefit_period_id,
                    observed_value=row.status,
                    normalized_value={
                        "status": row.status,
                        "pps_score": row.pps_score,
                        "kps_score": row.kps_score,
                        "fast_stage": row.fast_stage,
                        "nyha_class": row.nyha_class,
                        "adl_level": row.adl_level,
                        "adl_dependency_count": row.adl_dependency_count,
                        "primary_diagnosis": row.primary_diagnosis,
                        # eligibility_recommendation intentionally omitted --
                        # see class docstring.
                        "discipline": row.discipline,
                        "form_type": row.form_type,
                        "translation_accepted": row.translation_accepted,
                    },
                    recorded_at=recorded_at,
                    effective_at=effective_at,
                    extraction_method="DIRECT_ORM_READ",
                    origin=EvidenceOrigin.AUTHORITATIVE_DATABASE,
                )
            )

        return items


class CertificationSourceAdapter(SourceAdapter):
    """
    Authoritative evidence source backed by app.models.certification.Certification
    -- the signed Certification/Recertification of Terminal Illness (CTI) and
    its supporting physician narrative captured during the DRAFT stage.

    Surfaces only what a physician documented (narrative, supporting
    evidence, decline indicators, signed status/role/date). Never surfaces or
    derives a certification/recertification/eligibility conclusion of its
    own -- that determination belongs solely to a future, explicitly
    clinician-reviewed Recertification Framework stage.
    """

    SOURCE_MODEL = "Certification"
    SOURCE_TABLE = "certifications"

    def fetch(
        self,
        session: Session,
        *,
        patient_id: UUID,
        tenant_id: UUID,
        benefit_period_id: Optional[UUID] = None,
        as_of: Optional[datetime] = None,
    ) -> list[ClinicalEvidenceItem]:
        query = session.query(Certification).filter(
            Certification.patient_id == patient_id,
            Certification.tenant_id == tenant_id,
        )
        if benefit_period_id is not None:
            query = query.filter(Certification.benefit_period_id == benefit_period_id)

        rows = query.order_by(
            Certification.effective_date.asc(),
            Certification.id.asc(),
        ).all()

        items: list[ClinicalEvidenceItem] = []
        for row in rows:
            # Certification has no created_at column (BaseModel is not used
            # here) -- signed_at is the only reliable "when was this
            # recorded" timestamp available on the model.
            recorded_at = _tz_aware(row.signed_at)
            effective_at = None
            if row.effective_date is not None:
                effective_at = datetime.combine(
                    row.effective_date, datetime.min.time(), tzinfo=timezone.utc
                )

            if as_of is not None and effective_at is not None and effective_at > as_of:
                continue

            source_reference = ClinicalSourceReference(
                source_type="DATABASE_RECORD",
                source_id=str(row.id),
                source_record_type="CERTIFICATION_RECORD",
                source_field="physician_narrative",
                source_recorded_at=recorded_at,
                source_effective_at=effective_at,
                source_author_id=str(row.signed_by_user_id) if row.signed_by_user_id else None,
                authentication_status=row.status,
                source_model=self.SOURCE_MODEL,
                source_table=self.SOURCE_TABLE,
                source_patient_id=row.patient_id,
                source_encounter_id=None,
                source_benefit_period_id=row.benefit_period_id,
                correction_status="SUPERSEDED" if row.superseded_by_id is not None else None,
                supersedes_record_id=None,
            )

            items.append(
                ClinicalEvidenceItem(
                    evidence_id=f"{self.SOURCE_TABLE}:{row.id}",
                    patient_id=patient_id,
                    concept_code="CERTIFICATION",
                    canonical_name="Certification of Terminal Illness",
                    status=EvidenceStatus.DOCUMENTED,
                    source_reference=source_reference,
                    encounter_id=None,
                    benefit_period_id=row.benefit_period_id,
                    observed_value=row.status,
                    normalized_value={
                        "cert_type": row.cert_type,
                        "status": row.status,
                        "signed_by_role": row.signed_by_role,
                        "physician_narrative": row.physician_narrative,
                        "supporting_evidence": row.supporting_evidence,
                        "clinical_decline_indicators": row.clinical_decline_indicators,
                        "expires_at": row.expires_at.isoformat() if row.expires_at else None,
                        "superseded_by_id": str(row.superseded_by_id) if row.superseded_by_id else None,
                        "superseded_at": row.superseded_at.isoformat() if row.superseded_at else None,
                    },
                    recorded_at=recorded_at,
                    effective_at=effective_at,
                    extraction_method="DIRECT_ORM_READ",
                    origin=EvidenceOrigin.AUTHORITATIVE_DATABASE,
                )
            )

        return items


class F2FEncounterSourceAdapter(SourceAdapter):
    """
    Authoritative evidence source backed by app.models.f2f_encounter.F2FEncounter
    -- the dedicated face-to-face functional-assessment encounter (the only
    source model in this codebase that carries ECOG performance status;
    RNRecertAssessment does not have ecog_score_* fields).

    Surfaces the previous/current score pairs (PPS, ECOG) exactly as
    recorded -- this adapter reports the two observed values as evidence,
    it never itself computes or labels a "decline"/"improvement"
    conclusion from the pair; that comparison belongs to a later,
    explicitly-labeled synthesis stage (see
    app/services/recertification_evidence_synthesis.py for the analogous
    pattern used elsewhere in this codebase).
    """

    SOURCE_MODEL = "F2FEncounter"
    SOURCE_TABLE = "f2f_encounters"

    def fetch(
        self,
        session: Session,
        *,
        patient_id: UUID,
        tenant_id: UUID,
        benefit_period_id: Optional[UUID] = None,
        as_of: Optional[datetime] = None,
    ) -> list[ClinicalEvidenceItem]:
        query = session.query(F2FEncounter).filter(
            F2FEncounter.patient_id == patient_id,
            F2FEncounter.tenant_id == tenant_id,
        )
        if benefit_period_id is not None:
            query = query.filter(F2FEncounter.benefit_period_id == benefit_period_id)

        rows = query.order_by(
            F2FEncounter.encounter_date.asc(),
            F2FEncounter.id.asc(),
        ).all()

        items: list[ClinicalEvidenceItem] = []
        for row in rows:
            recorded_at = _tz_aware(row.created_at)
            effective_at = None
            if row.encounter_date is not None:
                effective_at = datetime.combine(
                    row.encounter_date, datetime.min.time(), tzinfo=timezone.utc
                )

            if as_of is not None and effective_at is not None and effective_at > as_of:
                # Future-effective exclusion.
                continue

            author_id = row.attesting_provider_user_id or row.performed_by_user_id or row.created_by

            source_reference = ClinicalSourceReference(
                source_type="DATABASE_RECORD",
                source_id=str(row.id),
                source_record_type="F2F_ENCOUNTER",
                source_field="clinical_decline_summary",
                source_recorded_at=recorded_at,
                source_effective_at=effective_at,
                source_author_id=str(author_id) if author_id else None,
                authentication_status="ATTESTED" if row.attested_at is not None else "UNATTESTED",
                source_model=self.SOURCE_MODEL,
                source_table=self.SOURCE_TABLE,
                source_patient_id=row.patient_id,
                # F2FEncounter has no dedicated encounter_id field distinct
                # from its own primary key -- the row IS the encounter.
                source_encounter_id=None,
                source_benefit_period_id=row.benefit_period_id,
            )

            items.append(
                ClinicalEvidenceItem(
                    evidence_id=f"{self.SOURCE_TABLE}:{row.id}",
                    patient_id=patient_id,
                    concept_code="F2F_ENCOUNTER",
                    canonical_name="Face-to-Face Encounter",
                    status=EvidenceStatus.DOCUMENTED,
                    source_reference=source_reference,
                    encounter_id=None,
                    benefit_period_id=row.benefit_period_id,
                    observed_value=row.status,
                    normalized_value={
                        "status": row.status,
                        "performed_by_role": row.performed_by_role,
                        "kps_score": row.kps_score,
                        "pps_score_previous": row.pps_score_previous,
                        "pps_score_current": row.pps_score_current,
                        "ecog_score_previous": row.ecog_score_previous,
                        "ecog_score_current": row.ecog_score_current,
                        "fast_score": row.fast_score,
                        "nyha_class": row.nyha_class,
                        "adl_dependency_level": row.adl_dependency_level,
                        "adl_dependency_count": row.adl_dependency_count,
                        "is_bedbound": row.is_bedbound,
                        "weight_loss_lbs": float(row.weight_loss_lbs) if row.weight_loss_lbs is not None else None,
                        "oral_intake_decline": row.oral_intake_decline,
                        "dysphagia": row.dysphagia,
                        "hospitalizations_30d": row.hospitalizations_30d,
                        "oxygen_lpm_previous": float(row.oxygen_lpm_previous) if row.oxygen_lpm_previous is not None else None,
                        "oxygen_lpm_current": float(row.oxygen_lpm_current) if row.oxygen_lpm_current is not None else None,
                        "primary_diagnosis": row.primary_diagnosis,
                        "secondary_conditions": row.secondary_conditions,
                    },
                    recorded_at=recorded_at,
                    effective_at=effective_at,
                    extraction_method="DIRECT_ORM_READ",
                    origin=EvidenceOrigin.AUTHORITATIVE_DATABASE,
                )
            )

        return items
