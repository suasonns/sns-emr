# =========================================================
# FILE: app/models/plan_of_care_version.py
# PURPOSE: Plan of Care Version (audit + immutable history)
# STATUS: HARDENED / FK SAFE
# =========================================================

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    CheckConstraint,
    Index,
    Boolean,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.orm import foreign

from app.db.base import Base


class PlanOfCareVersion(Base):
    __tablename__ = "plan_of_care_versions"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "plan_of_care_id",
            "version_number",
            name="uq_poc_versions_per_plan",
        ),

        CheckConstraint(
            "status IN ('DRAFT','ACTIVE','FINALIZED','SUPERSEDED')",
            name="ck_poc_version_status",
        ),

        CheckConstraint(
            "source_kind IN ('ICA','RN_UPDATE','IDG_UPDATE','SYSTEM')",
            name="ck_poc_version_source",
        ),

        Index("ix_pocv_plan_id", "plan_of_care_id"),
        Index("ix_pocv_tenant_id", "tenant_id"),
        Index("ix_pocv_status", "status"),
        Index("ix_pocv_version_number", "version_number"),
        Index("ix_pocv_based_on_version_id", "based_on_version_id"),
        Index("ix_pocv_idg_review_id", "idg_review_id"),

        # Composite index for retrieval performance
        Index(
            "ix_pocv_plan_version_desc",
            "plan_of_care_id",
            "version_number",
        ),
    )

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    plan_of_care_id = Column(
        UUID(as_uuid=True),
        ForeignKey("plan_of_care.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    version_number = Column(
        Integer,
        nullable=False,
    )

    # lineage
    based_on_version_id = Column(
        UUID(as_uuid=True),
        ForeignKey("plan_of_care_versions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    status = Column(
        String(20),
        nullable=False,
        default="ACTIVE",
    )

    source_kind = Column(
        String(30),
        nullable=False,
        default="ICA",
    )

    change_reason = Column(
        Text,
        nullable=True,
    )

    generated_from = Column(
        JSONB,
        nullable=True,
    )

    idg_review_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    reviewed_in_idg = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    snapshot_json = Column(
        JSONB,
        nullable=False,
        default=lambda: {},
    )

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    created_by_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_by_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # relationships
    plan_of_care = relationship(
        "PlanOfCare",
        back_populates="versions",
        foreign_keys=[plan_of_care_id],
    )

    based_on_version = relationship(
        "PlanOfCareVersion",
        remote_side=[id],
        uselist=False,
        foreign_keys=[based_on_version_id],
    )

    problems = relationship(
        "POCProblem",
        back_populates="poc_version",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="POCProblem.sort_order",
    )

    physician_approvals = relationship(
        "PocPhysicianApproval",
        primaryjoin="PlanOfCareVersion.id == foreign(PocPhysicianApproval.poc_version_id)",
        lazy="selectin",
        viewonly=True,
    )