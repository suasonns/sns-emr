# models/clinical_reasoning_result.py

from __future__ import annotations

import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    Text,
)

from sqlalchemy.dialects.postgresql import (
    JSONB,
    UUID,
)

from app.db.base import Base


class ClinicalReasoningResult(Base):
    __tablename__ = "clinical_reasoning_results"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    tenant_id = Column(
        UUID(as_uuid=True),
        nullable=False,
    )

    patient_id = Column(
        UUID(as_uuid=True),
        nullable=False,
    )

    source_document_id = Column(
        UUID(as_uuid=True),
        nullable=True,
    )

    source_document_name = Column(
        String(255),
        nullable=True,
    )

    profile_key = Column(
        String(255),
        nullable=False,
    )

    interpretation_key = Column(
        String(255),
        nullable=False,
    )

    reasoning_category = Column(
        String(100),
        nullable=True,
    )

    severity_level = Column(
        String(50),
        nullable=True,
    )

    confidence = Column(
        String(50),
        nullable=False,
    )

    matched_evidence = Column(
        JSONB,
        nullable=False,
    )

    missing_evidence = Column(
        JSONB,
        nullable=True,
    )

    evidence_count = Column(
        Integer,
        nullable=True,
    )

    rationale = Column(
        Text,
        nullable=True,
    )

    clinical_summary = Column(
        Text,
        nullable=True,
    )

    recommended_diagnosis = Column(
        String(255),
        nullable=True,
    )

    recommended_icd10 = Column(
        String(50),
        nullable=True,
    )

    requires_rn_review = Column(
        Boolean,
        nullable=False,
    )

    requires_md_review = Column(
        Boolean,
        nullable=False,
    )

    requires_idg_review = Column(
        Boolean,
        nullable=False,
    )

    accepted_by = Column(
        UUID(as_uuid=True),
        nullable=True,
    )

    accepted_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    rejected_by = Column(
        UUID(as_uuid=True),
        nullable=True,
    )

    rejected_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    rejection_reason = Column(
        Text,
        nullable=True,
    )

    reasoning_version = Column(
        String(255),
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
    )