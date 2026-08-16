"""
Diagnosis sources.

Read by admission gating, NOE readiness and ICD intelligence via raw SQL. The
table was previously created by hand in the development database and by no
migration, so a fresh environment did not have it.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class DiagnosisSource(Base):
    __tablename__ = "diagnosis_sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Originating workflow, e.g. RN_IA, MD, REFERRAL.
    source = Column(String(50), nullable=False, index=True)

    # PRIMARY or SECONDARY.
    dx_type = Column(String(20), nullable=False, index=True)

    icd_code = Column(String(20), nullable=True, index=True)
    description = Column(Text, nullable=True)

    documented_at = Column(DateTime(timezone=True), nullable=True)

    is_active = Column(Boolean, nullable=False, server_default="true", index=True)

    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())

    __table_args__ = (
        Index(
            "ix_diagnosis_sources_patient_active",
            "patient_id",
            "dx_type",
            "is_active",
        ),
    )
