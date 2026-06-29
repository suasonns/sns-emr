from __future__ import annotations

import uuid

from sqlalchemy import Column, String, Integer, Date, DateTime, ForeignKey, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.base import Base


class VisitMinutes(Base):
    __tablename__ = "visit_minutes"

    # ---------------------------------------------------------
    # PRIMARY KEY
    # ---------------------------------------------------------
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # ---------------------------------------------------------
    # TENANT ISOLATION
    # ---------------------------------------------------------
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ---------------------------------------------------------
    # VISIT LINK
    # ---------------------------------------------------------
    visit_id = Column(
        UUID(as_uuid=True),
        ForeignKey("visits.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ---------------------------------------------------------
    # SERVICE DATA
    # ---------------------------------------------------------
    discipline = Column(
        String(32),
        nullable=False,
        doc="RN / LVN / HHA / PT / OT / ST / MSW",
    )

    service_date = Column(
        Date,
        nullable=False,
        index=True,
    )

    minutes = Column(
        Integer,
        nullable=False,
    )

    units = Column(
        Integer,
        nullable=False,
    )

    status = Column(
        String(32),
        nullable=False,
        default="DRAFT",
        doc="DRAFT / FINALIZED / VALIDATED",
    )

    # ---------------------------------------------------------
    # AUDIT FIELDS
    # ---------------------------------------------------------
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    created_by = Column(
        String(255),
        nullable=True,
    )

    # ---------------------------------------------------------
    # RELATIONSHIPS
    # ---------------------------------------------------------
    visit = relationship("Visit")
    tenant = relationship("Tenant")

    # ---------------------------------------------------------
    # CONSTRAINTS + INDEXES
    # ---------------------------------------------------------
    __table_args__ = (
        # ✅ data validation
        CheckConstraint("minutes >= 0", name="ck_visit_minutes_positive"),
        CheckConstraint("units >= 0", name="ck_visit_units_positive"),

        # ✅ performance
        Index(
            "ix_visit_minutes_visit_date",
            "visit_id",
            "service_date",
        ),
        Index(
            "ix_visit_minutes_tenant",
            "tenant_id",
        ),
    )