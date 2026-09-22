from __future__ import annotations

"""
Generic compliance-obligation tracking for the shared SNS compliance
framework (issue #145). A `ComplianceObligation` is any regulatory
deadline/requirement that is not already represented by a more specific
domain record (election addendum, HOPE submission, two-hour response,
IDG follow-up, etc.) -- e.g. a CDPH/CMS obligation with no existing home.

Deliberately NOT a replacement for app.models.task.Task: Task represents
operational clinical work items; ComplianceObligation represents a
regulatory deadline that may or may not be backed by a Task. See
source_record_type/source_record_id for linking to whatever record
actually created the obligation (a Task, an admission event, etc.).
"""

import uuid

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base

COMPLIANCE_OBLIGATION_STATUSES = (
    "OPEN",
    "IN_PROGRESS",
    "COMPLETED",
    "OVERDUE",
    "WAIVED",
    "VOIDED",
)


class ComplianceObligation(Base):
    __tablename__ = "compliance_obligations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    admission_id = Column(UUID(as_uuid=True), ForeignKey("admissions.id", ondelete="SET NULL"), nullable=True, index=True)
    benefit_period_id = Column(
        UUID(as_uuid=True),
        ForeignKey("benefit_periods.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Populated only when the obligation is specifically billing/certification-period scoped.",
    )

    obligation_type = Column(String(64), nullable=False, index=True)
    regulatory_basis = Column(String(255), nullable=True, doc="e.g. '42 CFR 418.24(b)', 'Title 22 Section 74820'")
    status = Column(String(20), nullable=False, server_default="OPEN")

    required_by_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    completion_evidence_reference = Column(String(255), nullable=True)

    assigned_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    source_record_type = Column(String(64), nullable=True)
    source_record_id = Column(UUID(as_uuid=True), nullable=True)

    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    patient = relationship("Patient")

    __table_args__ = (
        Index("ix_compliance_obligations_tenant_status_due", "tenant_id", "status", "required_by_at"),
        Index("ix_compliance_obligations_tenant_patient", "tenant_id", "patient_id"),
        CheckConstraint(
            "status IN ('OPEN','IN_PROGRESS','COMPLETED','OVERDUE','WAIVED','VOIDED')",
            name="ck_compliance_obligations_status",
        ),
        CheckConstraint(
            "status != 'COMPLETED' OR completed_at IS NOT NULL",
            name="ck_compliance_obligations_completed_requires_timestamp",
        ),
    )


class ComplianceAuditEvent(Base):
    """Domain audit trail for generic compliance-obligation lifecycle events."""

    __tablename__ = "compliance_audit_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    compliance_obligation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("compliance_obligations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    admission_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    event_type = Column(String(50), nullable=False, index=True)
    actor_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    actor_account_discipline = Column(String(50), nullable=True)
    prior_value = Column(JSONB, nullable=True)
    new_value = Column(JSONB, nullable=True)
    reason = Column(Text, nullable=True)
    event_metadata = Column("metadata", JSONB, nullable=True)
    correlation_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)

    __table_args__ = (
        Index(
            "ix_compliance_audit_events_tenant_event_created",
            "tenant_id",
            "event_type",
            "created_at",
        ),
        CheckConstraint(
            "event_type IN ("
            "'REQUIREMENT_CREATED','DEADLINE_CALCULATED','ASSIGNED','DEADLINE_MISSED',"
            "'RECORD_CORRECTED','RECORD_FINALIZED','RECORD_REOPENED'"
            ")",
            name="ck_compliance_audit_events_type",
        ),
    )
