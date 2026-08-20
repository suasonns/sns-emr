from __future__ import annotations

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class FaxLog(BaseModel):
    """
    Fax transmission record for orders (physician orders, comfort packs,
    DME/supply requests, etc.) sent to a pharmacy, DME vendor, or physician.

    Architecture note: `provider` + `provider_reference` make this pluggable
    for a real fax gateway (SRFax, Sfax, Phaxio/Sinch, etc.) later without
    changing callers — same pattern used for the drug-safety JSON dataset
    (curated now, swappable for a licensed feed later). Today `provider`
    defaults to "SIMULATED": the fax is logged, a printable document is
    generated, and status starts at QUEUED — everything an agency needs to
    prove a fax was prepared/sent, without requiring a paid fax API key yet.
    """

    __tablename__ = "fax_logs"

    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # MEDICATION | PATIENT_ORDER | ORDER_SET (whole current order list)
    subject_type = Column(String(32), nullable=False)
    subject_id = Column(UUID(as_uuid=True), nullable=True)

    recipient_name = Column(String(255), nullable=False)
    recipient_fax_number = Column(String(32), nullable=False)

    # QUEUED | SENT | FAILED
    status = Column(String(32), nullable=False, server_default="QUEUED")

    provider = Column(String(32), nullable=False, server_default="SIMULATED")
    provider_reference = Column(String(128), nullable=True)

    document_summary = Column(Text, nullable=True)
    failure_reason = Column(Text, nullable=True)

    sent_at = Column(DateTime(timezone=True), nullable=True)

    patient = relationship("Patient")
