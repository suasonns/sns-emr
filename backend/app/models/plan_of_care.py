from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Column, DateTime, String, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class PlanOfCare(Base):
    """
    Enterprise-grade Plan of Care.

    Purpose:
    - Represents patient-level hospice Plan of Care (POC)
    - Tracks active plan and links to versions

    Compliance:
    - MUST reflect current plan state
    - MUST support traceability of updates
    - MUST preserve historical versions (audit requirement)
    """

    __tablename__ = "plan_of_care"

    __table_args__ = (
        Index("idx_poc_patient_id", "patient_id"),
        Index("idx_poc_tenant_id", "tenant_id"),
        Index("idx_poc_status", "status"),
    )

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )

    patient_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True
    )

    tenant_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True
    )

    # ✅ Controlled lifecycle status
    status = Column(
        String,
        nullable=False,
        default="ACTIVE",  # ACTIVE | INACTIVE | ARCHIVED
    )

    # ✅ pointer to current active version
    current_version_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        index=True
    )

    # ✅ RELATIONSHIP (CRITICAL FIX)
    versions = relationship(
        "PlanOfCareVersion",
        back_populates="plan_of_care",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="PlanOfCareVersion.created_at.desc()",
    )

    # ✅ audit fields
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    created_by_user_id = Column(
        UUID(as_uuid=True),
        nullable=True
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )