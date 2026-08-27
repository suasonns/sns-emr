from __future__ import annotations

import uuid

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
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

    # Real CMS Medicare Secondary Payer (MSP) value code (e.g. "12"
    # Working Aged/GHP, "15" Workers' Comp, "47" Liability). NULL when
    # this payer has no MSP relationship to Medicare (it either IS
    # Medicare, or is a payer with no COB claim against Medicare).
    msp_type_code = Column(String(2), nullable=True)

    # Explicit coordination-of-benefits sequence (1=primary, 2=secondary,
    # 3=tertiary...). Used instead of/alongside is_primary to resolve
    # multi-payer ordering unambiguously -- see
    # app/billing/services/msp_validation_service.py.
    priority_order = Column(Integer, nullable=True)

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