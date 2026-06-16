from __future__ import annotations

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
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

    # DB is actually varchar, so model must match DB
    id = Column(String, primary_key=True)

    # DB is actually varchar, not UUID
    patient_id = Column(
        String,
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

    # IMPORTANT:
    # Use explicit cast for the legacy varchar -> uuid join.
    # Use viewonly=True to avoid unsafe writes through a mismatched FK.
    # Use lazy="noload" to prevent circular JSON recursion:
    # Patient -> payers -> patient -> payers -> ...
    patient = relationship(
        "Patient",
        primaryjoin="cast(foreign(PatientPayer.patient_id), UUID(as_uuid=True)) == Patient.id",
        back_populates="payers",
        viewonly=True,
        lazy="noload",
    )