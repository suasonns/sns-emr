from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class PatientIssue(Base):
    __tablename__ = "patient_issues"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category = Column(String(64), nullable=False)
    description = Column(Text, nullable=False)
    identified_date = Column(Date, nullable=False)
    identified_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    status = Column(
        String(16),
        nullable=False,
        default="OPEN",
        server_default=text("'OPEN'"),
        index=True,
    )
    outcome_notes = Column(Text, nullable=True)
    resolved_date = Column(Date, nullable=True)
    resolved_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ---------------------------------------------------------
    # Interdisciplinary continuity workflow (MSW/CHAPLAIN/VOLUNTEER)
    # additive columns. `status` above is UNCHANGED and remains
    # authoritative for existing callers -- these are a richer,
    # independently-populated gradation used only by the continuity
    # workflow; do not repurpose or remove `status`.
    # ---------------------------------------------------------
    issue_domain = Column(String(32), nullable=True, index=True)
    clinical_status = Column(String(20), nullable=True, index=True)
    severity_or_risk = Column(String(20), nullable=True)
    monitoring_owner_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    monitoring_owner_role = Column(String(32), nullable=True)
    related_discipline_service_id = Column(
        UUID(as_uuid=True), ForeignKey("patient_discipline_services.id", ondelete="SET NULL"), nullable=True, index=True
    )
    related_refusal_event_id = Column(
        UUID(as_uuid=True), ForeignKey("patient_discipline_service_events.id", ondelete="SET NULL"), nullable=True
    )
    latest_assessment_id = Column(UUID(as_uuid=True), nullable=True)
    idg_review_required = Column(Boolean, nullable=False, server_default=text("false"))
    next_review_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=text("now()"),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=text("now()"),
    )

    __table_args__ = (
        Index("ix_patient_issues_tenant_patient_identified_date", "tenant_id", "patient_id", "identified_date"),
    )
