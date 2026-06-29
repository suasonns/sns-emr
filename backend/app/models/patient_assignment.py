from __future__ import annotations

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import Enum as SQLAEnum

from app.models.base import BaseModel
from app.models.enums import Discipline
from app.models.tenant_mixin import TenantScopedMixin


class PatientAssignment(TenantScopedMixin, BaseModel):
    """
    Patient Assignment Model

    PURPOSE:
    - Tracks interdisciplinary team assignments per patient
    - Supports RN case manager / primary assignment
    - Preserves active and historical assignment state
    """

    __tablename__ = "patient_assignments"

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
    # CORE REFERENCES
    # ---------------------------------------------------------
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

    # ---------------------------------------------------------
    # DISCIPLINE
    # ---------------------------------------------------------
    discipline = Column(
        SQLAEnum(
            Discipline,
            name="assignment_discipline_enum",
            create_constraint=False,
            create_type=False,
        ),
        nullable=False,
    )

    # ---------------------------------------------------------
    # ASSIGNMENT CONTROL
    # ---------------------------------------------------------
    is_primary = Column(
        Boolean,
        nullable=False,
        server_default="false",
    )

    active = Column(
        Boolean,
        nullable=False,
        server_default="true",
    )

    status = Column(
        String(16),
        nullable=False,
        server_default="ASSIGNED",
    )

    service_area = Column(String(64), nullable=True)

    note = Column(Text, nullable=True)

    # ---------------------------------------------------------
    # AUDIT FIELDS
    # ---------------------------------------------------------
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

    deactivated_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    # ---------------------------------------------------------
    # RELATIONSHIPS
    # ---------------------------------------------------------
    patient = relationship(
        "Patient",
        back_populates="assignments",
    )

    user = relationship(
        "User",
        foreign_keys=[user_id],
    )

    assigned_by_user = relationship(
        "User",
        foreign_keys=[assigned_by],
    )

    # ---------------------------------------------------------
    # INDEXES
    # ---------------------------------------------------------
    __table_args__ = (
        Index(
            "ix_patient_assignments_patient_active",
            "patient_id",
            "active",
        ),
        Index(
            "ix_patient_assignments_user_active",
            "user_id",
            "active",
        ),
        Index(
            "ix_patient_assignments_patient_discipline",
            "patient_id",
            "discipline",
        ),
    )

    # ---------------------------------------------------------
    # BUSINESS HELPERS
    # ---------------------------------------------------------
    def deactivate(self) -> None:
        self.active = False
        self.status = "INACTIVE"
        self.deactivated_at = func.now()

    def set_primary(self) -> None:
        self.is_primary = True