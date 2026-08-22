from __future__ import annotations

import uuid

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import BaseModel


class F2FEncounter(BaseModel):
    __tablename__ = "f2f_encounters"

    # -----------------------------------------------------
    # CORE IDENTIFIERS
    # -----------------------------------------------------
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id"),
        nullable=False,
        index=True,
    )

    benefit_period_id = Column(
        UUID(as_uuid=True),
        ForeignKey("benefit_periods.id"),
        nullable=False,
        index=True,
    )

    # -----------------------------------------------------
    # ENCOUNTER INFO
    # -----------------------------------------------------
    encounter_date = Column(Date, nullable=False)

    # F2F performer = hospice physician or hospice NP
    performed_by_role = Column(String, nullable=False)   # MD or NP
    performed_by_user_id = Column(UUID(as_uuid=True), nullable=True)

    # -----------------------------------------------------
    # STRUCTURED CLINICAL FINDINGS (ADR / RECERT DEFENSIBLE)
    # -----------------------------------------------------
    # Functional scoring
    kps_score = Column(Integer, nullable=True)
    pps_score_previous = Column(Integer, nullable=True)
    pps_score_current = Column(Integer, nullable=True)

    # Disease-specific scoring
    fast_score = Column(String, nullable=True)
    nyha_class = Column(String, nullable=True)

    # ADL / functional dependency
    adl_dependency_level = Column(String, nullable=True)
    adl_dependency_count = Column(Integer, nullable=True)
    is_bedbound = Column(Boolean, nullable=True)

    # Additional decline markers
    weight_loss_lbs = Column(Numeric, nullable=True)
    oral_intake_decline = Column(Boolean, nullable=True)
    dysphagia = Column(Boolean, nullable=True)
    hospitalizations_30d = Column(Integer, nullable=True)
    oxygen_lpm_previous = Column(Numeric, nullable=True)
    oxygen_lpm_current = Column(Numeric, nullable=True)

    primary_diagnosis = Column(Text, nullable=True)
    secondary_conditions = Column(Text, nullable=True)
    clinical_decline_summary = Column(Text, nullable=True)

    # -----------------------------------------------------
    # NARRATIVE
    # -----------------------------------------------------
    # Must be individualized, not generic boilerplate
    summary = Column(Text, nullable=True)

    # -----------------------------------------------------
    # F2F ATTESTATION
    # -----------------------------------------------------
    # CMS distinguishes F2F attestation from CTI certification
    attested_at = Column(DateTime, nullable=True)
    attesting_provider_user_id = Column(UUID(as_uuid=True), nullable=True)

    # -----------------------------------------------------
    # STATUS / FINALIZATION
    # -----------------------------------------------------
    status = Column(String, nullable=False, default="DRAFT", index=True)
    finalized_at = Column(DateTime, nullable=True)


class F2FEncounterStatusEvent(BaseModel):
    """
    Append-only, structured audit trail of every F2FEncounter status
    transition (DRAFT -> FINALIZED). Distinct from the generic AuditLog so
    the F2F performer/attestation history is directly queryable for survey
    evidence without parsing free-form JSON metadata. Never updated or
    deleted.
    """

    __tablename__ = "f2f_encounter_status_events"

    # Overrides BaseModel.created_by: this table's migration
    # (t9u0v1w2x3y4_f2f_phase1_lifecycle) created a plain nullable UUID
    # column with no FK/index, unlike most BaseModel-derived tables.
    created_by = Column(UUID(as_uuid=True), nullable=True)

    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    f2f_encounter_id = Column(
        UUID(as_uuid=True),
        ForeignKey("f2f_encounters.id", ondelete="CASCADE"),
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
