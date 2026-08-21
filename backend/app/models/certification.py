import uuid
from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Certification(BaseModel):
    """
    Certification of Terminal Illness (CTI) / Recertification.

    Phase 1 lifecycle expansion (owner directive 2026-08-21 — additive only,
    existing literals preserved):

        DRAFT -> PENDING_SIGNATURE -> FINALIZED -> [SUPERSEDED by next cert]

    DRAFT/PENDING_SIGNATURE are new lifecycle stages capturing the required
    physician narrative and supporting clinical/LCD evidence *before*
    signature; a bare "FINALIZED" cert (the only status previously used) is
    still fully supported for existing records.

    CTI signing authority is physician-level ONLY per SNS standard:
    MEDICAL_DIRECTOR, MEDICAL_DIRECTOR_DESIGNEE (aliases to MEDICAL_DIRECTOR),
    ATTENDING_PHYSICIAN, HOSPICE_PHYSICIAN. Nurse Practitioners and Physician
    Assistants are NOT authorized to sign a CTI (they may perform/sign F2F
    encounters, which is a distinct workflow/authority — see
    app/services/f2f_service.py). See certification_service.CTI_SIGNER_ROLES.
    `signed_by_role` records the *actual authenticated* role at signing time
    (never a client-supplied value) for audit/survey defensibility.
    """

    __tablename__ = "certifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True)
    benefit_period_id = Column(UUID(as_uuid=True), ForeignKey("benefit_periods.id"), nullable=False, index=True)

    cert_type = Column(String, nullable=False)  # INITIAL or RECERT
    signed_at = Column(DateTime, nullable=False)
    effective_date = Column(Date, nullable=False)

    signed_by_role = Column(String, nullable=False)  # MEDICAL_DIRECTOR | ATTENDING_PHYSICIAN | HOSPICE_PHYSICIAN
    signed_by_user_id = Column(UUID(as_uuid=True), nullable=True)

    # DRAFT | PENDING_SIGNATURE | FINALIZED | SUPERSEDED
    status = Column(String, nullable=False, default="FINALIZED")

    # --- Phase 1 lifecycle expansion (additive, 2026-08-21) ---

    # Physician narrative supporting the terminal prognosis (CMS/LCD
    # requires patient-specific evidence — clinical decline, functional
    # status, comorbidities, disease-specific indicators — not conclusions
    # alone) and structured/free-text supporting evidence, captured during
    # the DRAFT stage before signature.
    physician_narrative = Column(Text, nullable=True)
    supporting_evidence = Column(Text, nullable=True)
    clinical_decline_indicators = Column(Text, nullable=True)
    narrative_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    narrative_at = Column(DateTime(timezone=True), nullable=True)

    # Coverage-period end this certification supports (= benefit_period.end_date
    # at finalize time) — record-keeping only; a signed CTI remains a valid
    # legal record after its benefit period ends, it just needs a subsequent
    # recert to keep the patient's hospice benefit active (see
    # dashboard_service cti_due_missing / cti_expiring widgets).
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # Set when a later cert (next benefit period's recert) is finalized for
    # the same patient, chaining the certification history.
    superseded_by_id = Column(UUID(as_uuid=True), ForeignKey("certifications.id"), nullable=True)
    superseded_at = Column(DateTime(timezone=True), nullable=True)

    patient = relationship("Patient", foreign_keys=[patient_id])


class CertificationStatusEvent(BaseModel):
    """
    Append-only, structured audit trail of every Certification status
    transition (DRAFT -> PENDING_SIGNATURE -> FINALIZED -> SUPERSEDED).
    Distinct from the generic AuditLog so the CTI signature/narrative
    history is directly queryable for survey evidence without parsing
    free-form JSON metadata. Never updated or deleted.
    """

    __tablename__ = "certification_status_events"

    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    certification_id = Column(
        UUID(as_uuid=True),
        ForeignKey("certifications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    from_status = Column(String(32), nullable=True)
    to_status = Column(String(32), nullable=False)

    changed_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    changed_by_role = Column(String(64), nullable=True)
    changed_at = Column(DateTime(timezone=True), nullable=False)

    reason = Column(Text, nullable=True)
    automatic = Column(Boolean, nullable=False, server_default="false")
    evidence = Column(Text, nullable=True)