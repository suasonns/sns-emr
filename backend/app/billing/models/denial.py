from __future__ import annotations

import uuid

from sqlalchemy import (
    Column,
    String,
    Numeric,
    Date,
    ForeignKey,
    Index,
    DateTime,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.base import Base


class Denial(Base):
    """
    Real, persisted denial record backing the Denials & Appeals page (both
    the Biller's Dashboard and the owner's Tenant Analytics financials/
    billing mirror). Created automatically by
    app.services.payment_service.post_payments_from_835 whenever an 835
    remittance line is detected as a hard denial (see
    payment_service.DENIAL_CARC_CODES / _is_denied), so this table always
    reflects a real payer response -- never a guessed/fabricated value.

    One Denial per Payment posting that triggered it; a Claim can end up
    with more than one Denial row over its life (e.g. resubmit -> denied
    again), which is intentional -- each is its own payer determination.
    """

    __tablename__ = "denials"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    claim_id = Column(
        UUID(as_uuid=True),
        ForeignKey("claims.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    payment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("payments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="The 835 Payment line that produced this denial, if posted electronically.",
    )

    carc_code = Column(
        String(8),
        nullable=True,
        index=True,
        doc="Primary CARC code driving the denial (see PaymentAdjustment for the full set).",
    )

    reason_description = Column(Text, nullable=True)

    denied_amount = Column(Numeric(12, 2), nullable=True)

    denial_date = Column(Date, nullable=True)

    appeal_deadline = Column(
        Date,
        nullable=True,
        doc="Payer's filing deadline for an appeal, when known/configured.",
    )

    status = Column(
        String(32),
        nullable=False,
        default="OPEN",
        server_default=text("'OPEN'"),
        index=True,
        doc="OPEN / APPEALED / OVERTURNED / UPHELD / WRITTEN_OFF",
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=func.now(),
    )

    tenant = relationship("Tenant")
    claim = relationship("Claim")
    payment = relationship("Payment")
    appeals = relationship(
        "Appeal", back_populates="denial", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_denial_tenant_status", "tenant_id", "status"),
    )
