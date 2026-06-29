from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class PlanOfCare(Base):
    """
    Enterprise-grade Plan of Care.

    Purpose:
    - Represents patient-level hospice Plan of Care (POC)
    - Tracks active plan and links to versions (future structure)

    Compliance:
    - MUST reflect current plan state
    - MUST support traceability of updates
    - MUST be auditable over time
    """

    __tablename__ = "plan_of_care"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    patient_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    status = Column(String, nullable=False, default="ACTIVE")

    # 🔥 TEMPORARY: FK REMOVED (stabilization phase)
    current_version_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by_user_id = Column(UUID(as_uuid=True), nullable=True)

    # 🔥 TEMP: relationship disabled until version table is added
    # versions = relationship(
    #     "PlanOfCareVersion",
    #     back_populates="plan_of_care",
    # )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
