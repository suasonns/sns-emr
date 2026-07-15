from __future__ import annotations

import uuid

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class PatientPayer(Base):
    __tablename__ = "patient_payers"

    __table_args__ = (
        Index("ix_patient_payers_patient_id", "patient_id"),
        Index("ix_patient_payers_subscriber", "subscriber_id"),
    )

    # ✅ FIXED: UUID PRIMARY KEY
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # ✅ FIXED: UUID FOREIGN KEY
    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id"),
        nullable=False,
        index=True,
    )

    payer_name = Column(String, nullable=False)
    payer_type = Column(String, nullable=False)

    subscriber_id = Column(String, nullable=True)
    subscriber_id_type = Column(String, nullable=True)

    facility_name = Column(String(255), nullable=True)

    effective_start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)

    is_primary = Column(
        Boolean,
        nullable=True,
        server_default=text("true"),
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=True,
        server_default=text("now()"),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=True,
        server_default=text("now()"),
    )

    created_by = Column(
        UUID(as_uuid=True),
        nullable=True,
    )

    # ✅ FIXED: NORMAL FK RELATIONSHIP
    patient = relationship(
        "Patient",
        back_populates="payers",
        lazy="noload",
    )