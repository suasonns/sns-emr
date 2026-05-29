from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Boolean, CheckConstraint, text
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

    # Optional: light constraints that are safe and DB-portable.
    # (Do NOT add strict clinical enums here unless you also enforce in API/service.)
    __table_args__ = (
        CheckConstraint("status <> ''", name="ck_visits_status_not_blank"),
        CheckConstraint("visit_type <> ''", name="ck_visits_visit_type_not_blank"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

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

    visit_type = Column(String(32), nullable=False, index=True)

    visit_discipline = Column(String(32), nullable=True, index=True)

    status = Column(String(32), nullable=False, index=True)

    visit_datetime = Column(DateTime(timezone=False), nullable=False, index=True)

    # NEW: visit_mode (matches your "add visit_mode" migration intent)
    # Defaults to IN_PERSON to keep inserts backwards compatible.
    visit_mode = Column(String(32), nullable=False, index=True, server_default=text("'IN_PERSON'"))

    is_supervisory = Column(Boolean, nullable=False, server_default=text("false"))

    acuity_state_at_visit = Column(String(32), nullable=True)

    finalized_at = Column(DateTime(timezone=False), nullable=True)

    finalized_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    chha_poc_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    created_at = Column(DateTime(timezone=False), server_default=func.now(), nullable=False)

    updated_at = Column(
        DateTime(timezone=False),
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