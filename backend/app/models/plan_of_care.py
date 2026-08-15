# =========================================================
# FILE: app/models/plan_of_care.py
# PURPOSE: Plan of Care root model (stable)
# STATUS: HARDENING PHASE SAFE
# =========================================================

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    Column,
    DateTime,
    String,
    Index,
    ForeignKey,
    CheckConstraint,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class PlanOfCare(Base):
    __tablename__ = "plan_of_care"

    __table_args__ = (
        Index("ix_poc_patient_id", "patient_id"),
        Index("ix_poc_tenant_id", "tenant_id"),
        Index("ix_poc_admission_id", "admission_id"),
        Index("ix_poc_status", "status"),

        # Composite index for performance
        Index("ix_poc_tenant_admission", "tenant_id", "admission_id"),

        UniqueConstraint(
            "tenant_id",
            "admission_id",
            name="uq_poc_one_per_admission_per_tenant",
        ),

        CheckConstraint(
            "status IN ('ACTIVE','INACTIVE','ARCHIVED')",
            name="ck_poc_status",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    admission_id = Column(
        UUID(as_uuid=True),
        ForeignKey("admissions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    status = Column(
        String(20),
        nullable=False,
        default="ACTIVE",
    )

    current_version_id = Column(
        UUID(as_uuid=True),
        ForeignKey("plan_of_care_versions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    versions = relationship(
        "PlanOfCareVersion",
        back_populates="plan_of_care",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="PlanOfCareVersion.version_number.desc()",
        foreign_keys="PlanOfCareVersion.plan_of_care_id",
    )

    current_version = relationship(
        "PlanOfCareVersion",
        foreign_keys=[current_version_id],
        post_update=True,
        uselist=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    created_by_user_id = Column(
        UUID(as_uuid=True),
        nullable=True,
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    updated_by_user_id = Column(
        UUID(as_uuid=True),
        nullable=True,
    )