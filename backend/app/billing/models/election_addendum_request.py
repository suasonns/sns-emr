from __future__ import annotations

import uuid

from sqlalchemy import Column, Date, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class ElectionAddendumRequest(Base):
    """
    A real, logged request for the CMS Hospice Election Statement Addendum
    (42 CFR 418.24(b)) -- itemizing which of the patient's conditions/
    services the hospice has determined are unrelated to the terminal
    illness. Tracks the real request date, who requested it, and (once it
    happens) the real delivery date, so
    election_addendum_service.compute_addendum_compliance() can evaluate
    the CMS 5-day / 72-hour furnishing deadline against real dates only.
    """

    __tablename__ = "election_addendum_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    requested_date = Column(Date, nullable=False)

    requested_by = Column(
        String(32),
        nullable=False,
        doc="PATIENT_OR_REPRESENTATIVE / NON_HOSPICE_PROVIDER / MEDICARE_CONTRACTOR",
    )

    delivered_date = Column(Date, nullable=True)

    not_required_reason = Column(
        String(255),
        nullable=True,
        doc="Documented reason the furnishing requirement no longer applies (e.g. request withdrawn).",
    )

    created_by = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    patient = relationship("Patient")

    __table_args__ = (
        Index("ix_election_addendum_requests_tenant_patient", "tenant_id", "patient_id"),
    )
