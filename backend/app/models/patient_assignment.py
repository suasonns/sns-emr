from __future__ import annotations

from sqlalchemy import Column, ForeignKey, String, Boolean, DateTime, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.types import Enum as SQLAEnum

from app.models.base import BaseModel
from app.models.tenant_mixin import TenantScopedMixin
from app.models.enums import Discipline


class PatientAssignment(TenantScopedMixin, BaseModel):
    """
    Patient Assignment Model (Production Grade)

    PURPOSE:
    - Tracks interdisciplinary team assignments per patient
    - Supports RN case manager (primary assignment)
    - Differentiates active vs historical assignments

    COMPLIANCE ALIGNMENT:
    - Supports IDG structure (RN, LVN, MSW, Chaplain)
    - Enables clear accountability (survey-ready)
    """

    __tablename__ = "patient_assignments"

    # =====================================================
    # CORE REFERENCES
    # =====================================================
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )

    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # =====================================================
    # DISCIPLINE (STRICT ENUM — IMPORTANT)
    # =====================================================
    discipline = Column(
        SQLAEnum(Discipline, name="assignment_discipline_enum"),
        nullable=False,
    )

    # =====================================================
    # ASSIGNMENT CONTROL (CRITICAL FIELDS)
    # =====================================================
    is_primary = Column(
        Boolean,
        nullable=False,
        server_default="false",
        doc="True if this is the primary RN / case manager",
    )

    active = Column(
        Boolean,
        nullable=False,
        server_default="true",
        doc="True if assignment is active",
    )

    status = Column(
        String(16),
        nullable=False,
        server_default="ASSIGNED",
        doc="ASSIGNED / INACTIVE / REMOVED",
    )

    service_area = Column(String(64), nullable=True)

    # =====================================================
    # AUDIT FIELDS
    # =====================================================
    assigned_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    assigned_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )

    note = Column(Text, nullable=True)

    # =====================================================
    # RELATIONSHIPS
    # =====================================================
    patient = relationship("Patient", back_populates="assignments")

    user = relationship("User", foreign_keys=[user_id])

    assigned_by_user = relationship("User", foreign_keys=[assigned_by])

    # =====================================================
    # BUSINESS HELPERS (SAFE, NON-AUTOMATIC)
    # =====================================================

    def deactivate(self):
        """
        Soft deactivate assignment (historical)
        """
        self.active = False
        self.status = "INACTIVE"

    def set_primary(self):
        """
        Mark as primary (must enforce uniqueness in service layer)
        """
        self.is_primary = True
