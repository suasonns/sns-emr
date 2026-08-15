from __future__ import annotations

from uuid import uuid4

from sqlalchemy import (
    Column,
    String,
    DateTime,
    ForeignKey,
    Text,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class AdmissionStatusHistory(Base):
    """
    Admission Status Audit Trail

    Purpose:
    - Track every admission status movement
    - Preserve workflow history
    - Support QA + survey readiness
    - Provide medico-legal audit evidence
    """

    __tablename__ = "admission_status_history"

    # ---------------------------------------------------------
    # Identity
    # ---------------------------------------------------------

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    admission_id = Column(
        UUID(as_uuid=True),
        ForeignKey("admissions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ---------------------------------------------------------
    # Transition
    # ---------------------------------------------------------

    previous_status = Column(
        String(32),
        nullable=True,  # ✅ FIXED
        index=True,
    )

    new_status = Column(
        String(32),
        nullable=False,
        index=True,
    )

    # ---------------------------------------------------------
    # Audit
    # ---------------------------------------------------------

    changed_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    changed_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    # ---------------------------------------------------------
    # Reasoning
    # ---------------------------------------------------------

    reason = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    # ---------------------------------------------------------
    # Relationships
    # ---------------------------------------------------------

    patient = relationship(
        "Patient",
        back_populates="admission_status_history",
    )

    user = relationship(
        "User",
        foreign_keys=[changed_by],
    )
    
    admission = relationship(
        "Admission",
        back_populates="status_history",
    )
    
    # ---------------------------------------------------------
    # Indexes
    # ---------------------------------------------------------

    __table_args__ = (
        Index(
            "ix_adm_hist_patient_time",
            "patient_id",
            "changed_at",
        ),
        Index(
            "ix_adm_hist_tenant_patient",
            "tenant_id",
            "patient_id",
        ),
        Index(
            "ix_adm_hist_prev_new",
            "previous_status",
            "new_status",
        ),
    )