from __future__ import annotations

import uuid
from datetime import datetime, date
from typing import Optional

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    String,
    Boolean,
    CheckConstraint,
    Index,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.db.base import Base


class Visit(Base):
    """
    Enterprise-grade Visit model.

    Regulatory relevance:
    - CMS Hospice Conditions of Participation (CoPs)
    - RN supervisory visit enforcement
    - Survey-defensible visit finalization and audit trail

    IMPORTANT:
    - This model is STRUCTURE ONLY.
    - All business logic lives in the service layer.
    """

    __tablename__ = "visits"

    __table_args__ = (
        CheckConstraint("status <> ''", name="ck_visits_status_not_blank"),
        CheckConstraint("visit_type <> ''", name="ck_visits_visit_type_not_blank"),
        CheckConstraint("visit_mode <> ''", name="ck_visits_mode_not_blank"),

        Index(
            "ix_visits_patient_datetime",
            "patient_id",
            "visit_datetime",
        ),
    )

    # =========================================================
    # PRIMARY KEY
    # =========================================================

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # =========================================================
    # TENANCY / RELATIONSHIPS
    # =========================================================

    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    provider_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # =========================================================
    # VISIT CLASSIFICATION
    # =========================================================

    visit_type = Column(String(32), nullable=False, index=True)
    visit_discipline = Column(String(32), nullable=True, index=True)

    visit_mode = Column(
        String(32),
        nullable=False,
        index=True,
        server_default=text("'IN_PERSON'"),
    )

    status = Column(String(32), nullable=False, index=True)

    is_supervisory = Column(Boolean, nullable=False, server_default=text("false"))

    acuity_state_at_visit = Column(String(32), nullable=True)

    # ✅ ✅ ✅ NEW FORM ENGINE FIELD (CRITICAL)
    form_type = Column(String(64), nullable=True)

    # =========================================================
    # TIME TRACKING (FOR CC + BILLING)
    # =========================================================

    start_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)

    # =========================================================
    # TIMESTAMPS
    # =========================================================

    visit_datetime = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    finalized_at = Column(DateTime(timezone=True), nullable=True)

    # =========================================================
    # AUDIT TRAIL
    # =========================================================

    finalized_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    updated_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    deleted_at = Column(DateTime(timezone=True), nullable=True)

    deleted_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )

    # =========================================================
    # OPTIONAL / EXTENSIONS
    # =========================================================

    chha_poc_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    # =========================================================
    # COMPATIBILITY LAYER
    # =========================================================

    @property
    def visit_date(self) -> Optional[date]:
        """
        Backward-compatible alias for services expecting visit.visit_date.
        Derived from visit_datetime.
        """
        value = getattr(self, "visit_datetime", None)

        if isinstance(value, datetime):
            return value.date()

        if isinstance(value, date):
            return value

        return None