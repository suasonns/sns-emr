from __future__ import annotations

import uuid

from sqlalchemy import (
    Column,
    Numeric,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Index,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.base import Base


class HospiceCapRecord(Base):
    """
    Real, biller-entered inputs for the agency-level hospice aggregate cap
    (42 CFR 418.309). hospice_cap_service.compute_agency_cap_usage() needs
    `beneficiary_count` and `gross_reimbursement_collected` for a cap year,
    and this system has no visibility into either figure on its own:

    - `beneficiary_count` is a CMS/NGS cross-provider proportional count
      (a beneficiary who received hospice care from more than one agency
      in the cap year is split proportionally across those agencies) --
      it can only come from the agency's real NGS PS&R cap report.
    - `gross_reimbursement_collected` is the agency's actual paid claims
      total for the cap year, also sourced from the PS&R report or the
      agency's own remittance records.

    This table exists so a biller/admin can log those two real,
    externally-sourced numbers per cap year, instead of the app
    fabricating or guessing them. Until a record exists for a given cap
    year, cap usage for that year is "not yet configured" -- never a
    fabricated $0.00 or 100%.
    """

    __tablename__ = "hospice_cap_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    cap_year = Column(
        Integer,
        nullable=False,
        doc="Hospice cap year (Nov 1 - Oct 31 cap accounting year, identified by its starting calendar year).",
    )

    beneficiary_count = Column(
        Numeric(10, 4),
        nullable=False,
        doc="Real, NGS/PS&R-sourced proportional beneficiary count for this cap year (may carry decimals due to cross-provider proration).",
    )

    gross_reimbursement_collected = Column(
        Numeric(14, 2),
        nullable=False,
        doc="Real total Medicare hospice reimbursement collected by this agency for the cap year, per the PS&R report or remittance records.",
    )

    source_note = Column(
        String(500),
        nullable=True,
        doc="Where these figures came from, e.g. 'NGS PS&R report dated 2026-03-01'.",
    )

    updated_by = Column(String(255), nullable=True)

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    tenant = relationship("Tenant")

    __table_args__ = (
        UniqueConstraint("tenant_id", "cap_year", name="uq_hospice_cap_record_tenant_year"),
        Index("ix_hospice_cap_records_tenant_year", "tenant_id", "cap_year"),
    )
