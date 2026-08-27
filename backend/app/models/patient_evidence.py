"""
Unified Clinical Intelligence & Evidence Reconciliation Engine (UCIER)
-- Phase 1 foundation models.

Design rules (see docs/architecture/Unified Clinical Intelligence &
Evidence Reconciliation Engine.md):
    - Every source is harvestable.
    - Nothing observed is discarded.
    - Nothing harvested is anonymous.
    - Nothing elevated lacks evidence.
    - AI may harvest, organize, and flag. AI must never silently change
      diagnoses, plan of care, or problem status without a human review
      workflow.

`PatientEvidenceRecord` is the source-stamped evidence registry: one row
per piece of original documentation ingested by the harvester (a visit
note, a communication log entry, a CTI narrative, an F2F encounter
summary, etc). It always preserves the original text excerpt and full
provenance, even if no AI signal is ultimately produced from it.

`PatientHarvestedSignal` is the AI-extracted, structured candidate signal
tied back to exactly one evidence record. It carries its own review state
machine (NEW -> PENDING_REVIEW -> ACKNOWLEDGED / DISMISSED / ESCALATED)
so it also serves as the Phase 2 "signal registry" described in the
architecture doc, without needing a third table yet.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class PatientEvidenceRecord(Base):
    """Source-stamped evidence registry (patient_evidence_registry)."""

    __tablename__ = "patient_evidence_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # -----------------------------------------------------------
    # SOURCE PROVENANCE (mandatory per UCIER acceptance criteria)
    # -----------------------------------------------------------
    # source_type identifies which documentation source produced this
    # evidence record. Values used by the harvesters:
    #   CLINICAL_NOTE (covers RN/LVN/NP/MD/SC/MSW/LCSW/BSW visit notes,
    #     RN ICA, MSW ICA, SC ICA -- all routed through ClinicalNote),
    #   CHHA_VISIT_OUTCOME, COMMUNICATION_LOG, ON_CALL_LOG, INCIDENT_REPORT,
    #   IDG_NOTE, PLAN_OF_CARE_REVIEW, CERTIFICATION (CTI),
    #   F2F_ENCOUNTER, VOLUNTEER_NOTE, FACILITY_NOTIFICATION
    source_type = Column(String(64), nullable=False, index=True)
    source_record_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    visit_id = Column(UUID(as_uuid=True), ForeignKey("visits.id"), nullable=True, index=True)
    communication_log_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    discipline = Column(String(16), nullable=True, index=True)

    recorded_by_user_id = Column(UUID(as_uuid=True), nullable=True)
    recorded_by_name = Column(String(255), nullable=True)
    recorded_at = Column(DateTime(timezone=True), nullable=False)

    # Original documentation text this record was harvested from. Never
    # discarded, never anonymized, never edited by the AI extraction step.
    original_documentation = Column(Text, nullable=False)

    # -----------------------------------------------------------
    # HARVEST METADATA
    # -----------------------------------------------------------
    harvested_by = Column(String(64), nullable=False, server_default=text("'ai_evidence_harvester'"))
    harvested_at = Column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))

    # Whether AI extraction actually ran successfully against this record
    # (false if the AI service was unavailable/unconfigured -- the
    # evidence record is still preserved either way, per "nothing
    # observed is discarded").
    ai_extraction_completed = Column(Boolean, nullable=False, server_default=text("false"))
    ai_extraction_error = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    signals = relationship(
        "PatientHarvestedSignal",
        back_populates="evidence_record",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_evidence_records_patient_source", "patient_id", "source_type"),
        Index("ix_evidence_records_tenant_recorded_at", "tenant_id", "recorded_at"),
        UniqueConstraint(
            "tenant_id", "source_type", "source_record_id", name="uq_evidence_records_tenant_source"
        ),
    )


class PatientHarvestedSignal(Base):
    """AI-extracted candidate signal (patient_harvested_signals)."""

    __tablename__ = "patient_harvested_signals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    evidence_record_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patient_evidence_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Denormalized provenance copies for fast querying without a join
    # (still fully backed by evidence_record_id above).
    source_type = Column(String(64), nullable=False, index=True)
    source_discipline = Column(String(16), nullable=True, index=True)
    recorded_at = Column(DateTime(timezone=True), nullable=False)

    # -----------------------------------------------------------
    # SIGNAL CONTENT
    # -----------------------------------------------------------
    signal_key = Column(String(128), nullable=False, index=True)
    signal_text = Column(Text, nullable=False)
    original_text_excerpt = Column(Text, nullable=False)
    comparison_text = Column(Text, nullable=True)

    # UP / DOWN / STABLE / UNKNOWN -- direction of change, if any, that the
    # AI extraction identified relative to prior documentation.
    trend = Column(String(16), nullable=True)

    # Model-reported confidence 0.00-1.00. Never used to auto-elevate a
    # signal without human review -- informational only.
    confidence = Column(Numeric(3, 2), nullable=True)

    clinical_system = Column(String(64), nullable=True)

    # Validated StructuredFinding objects (see app.services.evidence.
    # structured_findings) extracted from this same signal's source text --
    # zero or more concept-code findings, each already passed through
    # validate_findings() so only registry-known concepts, allowed enum
    # values, and in-range numerics ever land here. This is what feeds the
    # RNICA structured-field auto-apply layer (blank-only, assertion-status
    # gated); it is stored independently of signal_text/original_text_excerpt
    # above so "no structured field mapped" (EVIDENCE_FOUND) is always
    # distinguishable from "at least one field mapped" (ASSESSMENT_DRAFTED)
    # without re-parsing free text. Empty list, never null, when nothing in
    # this excerpt maps to a known concept.
    structured_findings = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))

    # -----------------------------------------------------------
    # STRUCTURED FINDINGS PROCESSING STATE
    # -----------------------------------------------------------
    # Tracks whether the concept-aware structured_findings extraction
    # pipeline (app.services.evidence.structured_findings) has actually been
    # run against this row's source text -- an empty structured_findings
    # list alone is ambiguous between "never attempted" and "attempted, model
    # found nothing". PENDING -> COMPLETED | FAILED via harvest_service on
    # creation, and via structured_findings_reprocess_service for backfill /
    # retry of older rows. Rows created before this column existed are
    # migrated to PENDING so they become eligible for backfill.
    structured_findings_status = Column(
        String(24),
        nullable=False,
        default="PENDING",
        server_default=text("'PENDING'"),
    )
    structured_findings_attempts = Column(Integer, nullable=False, server_default=text("0"))
    structured_findings_last_attempted_at = Column(DateTime(timezone=True), nullable=True)
    structured_findings_last_error = Column(Text, nullable=True)

    requires_rn_review = Column(Boolean, nullable=False, server_default=text("true"))
    requires_idg_review = Column(Boolean, nullable=False, server_default=text("false"))
    requires_poc_review = Column(Boolean, nullable=False, server_default=text("false"))

    # -----------------------------------------------------------
    # REVIEW STATE MACHINE (doubles as Phase 2 signal registry)
    # -----------------------------------------------------------
    # NEW -> PENDING_REVIEW -> ACKNOWLEDGED | DISMISSED | ESCALATED
    review_status = Column(
        String(24),
        nullable=False,
        default="NEW",
        server_default=text("'NEW'"),
        index=True,
    )
    reviewed_by_user_id = Column(UUID(as_uuid=True), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    review_disposition_reason = Column(Text, nullable=True)

    linked_problem_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    evidence_record = relationship("PatientEvidenceRecord", back_populates="signals")

    __table_args__ = (
        Index("ix_harvested_signals_patient_status", "patient_id", "review_status"),
        Index("ix_harvested_signals_tenant_recorded_at", "tenant_id", "recorded_at"),
        Index("ix_harvested_signals_structured_findings_status", "structured_findings_status"),
    )
