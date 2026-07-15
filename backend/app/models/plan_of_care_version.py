from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class PlanOfCareVersion(Base):
    __tablename__ = "plan_of_care_versions"

    __table_args__ = (
        UniqueConstraint(
            "plan_of_care_id",
            "version_number",
            name="uq_plan_of_care_versions_plan_version",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    plan_of_care_id = Column(
        UUID(as_uuid=True),
        ForeignKey("plan_of_care.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    version_number = Column(
        Integer,
        nullable=False,
        index=True,
    )

    based_on_version_id = Column(
        UUID(as_uuid=True),
        ForeignKey("plan_of_care_versions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    snapshot_json = Column(
        JSONB,
        nullable=False,
        default=lambda: {},
    )

    approval_status = Column(
        String,
        nullable=False,
        default="PENDING",
        index=True,
    )

    approved_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    approved_by_user_id = Column(
        UUID(as_uuid=True),
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    created_by_user_id = Column(
        UUID(as_uuid=True),
        nullable=True,
    )

    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    plan_of_care = relationship(
        "PlanOfCare",
        back_populates="versions",
    )

    based_on_version = relationship(
        "PlanOfCareVersion",
        remote_side=[id],
        uselist=False,
    )

    physician_approvals = relationship(
        "PocPhysicianApproval",
        primaryjoin="PlanOfCareVersion.id==foreign(PocPhysicianApproval.poc_version_id)",
        lazy="selectin",
        viewonly=True,
    )