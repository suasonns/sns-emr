from __future__ import annotations

from sqlalchemy import Column, DateTime, ForeignKey, String, Boolean
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
    - All business logic (finalize rules, task creation, validation)
      lives in the service layer.
    """

    __tablename__ = "visits"

    # -------------------------------------------------
    # Identity
    # -------------------------------------------------
    id = Column(UUID(as_uuid=True), primary_key=True)

    # -------------------------------------------------
    # Core relationships
    # -------------------------------------------------
    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id"),
        nullable=False,
        index=True,
    )

    provider_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    # -------------------------------------------------
    # Visit semantics
    # -------------------------------------------------
    visit_type = Column(
        String(32),
        nullable=False,
        index=True,
    )
    # Normalized in API/service layer (RN, LVN, NP, MD, SW, CHAPLAIN, AIDE)

    status = Column(
        String(32),
        nullable=False,
        index=True,
    )
    # Values enforced in service layer (e.g., DRAFT, FINALIZED)

    # -------------------------------------------------
    # Timing
    # -------------------------------------------------
    visit_datetime = Column(
        DateTime(timezone=False),
        nullable=False,
        index=True,
    )

    # -------------------------------------------------
    # Compliance flags
    # -------------------------------------------------
    is_supervisory = Column(
        Boolean,
        nullable=False,
        server_default="false",
    )

    acuity_state_at_visit = Column(
        String(32),
        nullable=True,
    )

    # -------------------------------------------------
    # Finalization audit (LEGAL SNAPSHOT)
    # -------------------------------------------------
    finalized_at = Column(
        DateTime(timezone=False),
        nullable=True,
    )

    finalized_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    # -------------------------------------------------
    # CHHA Plan of Care linkage (if applicable)
    # -------------------------------------------------
    chha_poc_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    # -------------------------------------------------
    # Audit timestamps
    # -------------------------------------------------
    created_at = Column(
        DateTime(timezone=False),
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=False),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )