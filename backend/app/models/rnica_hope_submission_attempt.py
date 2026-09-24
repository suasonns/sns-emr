from __future__ import annotations

import uuid

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class RnicaHopeSubmissionAttempt(Base):
    """
    Child table preserving every individual HOPE submission/rejection/
    correction/resubmission attempt for an RnicaAssessment. This table
    records attempt history only -- it must never become a second owner
    of HOPE workflow/submission status (that remains
    RnicaAssessment.hope_workflow_status).
    """

    __tablename__ = "rnica_hope_submission_attempts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    rnica_assessment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("rnica_assessments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    attempt_number = Column(Integer, nullable=False)
    submitted_at = Column(DateTime(timezone=True), nullable=False)
    submission_number = Column(String(128), nullable=True)
    receipt_reference = Column(String(128), nullable=True)
    validation_status = Column(String(32), nullable=True)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)
    error_payload = Column(JSONB, nullable=True)
    warning_payload = Column(JSONB, nullable=True)
    correction_reason = Column(Text, nullable=True)
    supersedes_attempt_id = Column(
        UUID(as_uuid=True),
        ForeignKey("rnica_hope_submission_attempts.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    rnica_assessment = relationship("RnicaAssessment", backref="hope_submission_attempts")

    __table_args__ = (
        Index("ix_rnica_hope_submission_attempts_tenant_id", "tenant_id"),
        UniqueConstraint(
            "rnica_assessment_id",
            "attempt_number",
            name="uq_rnica_hope_submission_attempts_assessment_attempt",
        ),
        CheckConstraint("attempt_number > 0", name="ck_rnica_hope_submission_attempts_attempt_positive"),
        CheckConstraint(
            "accepted_at IS NULL OR rejected_at IS NULL",
            name="ck_rnica_hope_submission_attempts_accept_reject_mutually_exclusive",
        ),
        CheckConstraint(
            "supersedes_attempt_id IS NULL OR supersedes_attempt_id != id",
            name="ck_rnica_hope_submission_attempts_no_self_supersede",
        ),
    )
