from __future__ import annotations

import uuid

from sqlalchemy import Column, String, Numeric, ForeignKey, Index, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.base import Base


class PaymentAdjustment(Base):
    """
    One CAS (Claim Adjustment) line from an 835 -- the CARC (Claim
    Adjustment Reason Code) + group code + dollar amount that explains
    why billed != paid for a Payment. This is the real backing data for
    denial reasons on the Denials & Appeals page (CARC lookup happens in
    the API/service layer against a static reference table, not stored
    here).
    """

    __tablename__ = "payment_adjustments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    payment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("payments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    group_code = Column(
        String(4),
        nullable=True,
        doc="CO (Contractual Obligation) / PR (Patient Responsibility) / OA / PI / CR",
    )

    carc_code = Column(String(8), nullable=False)

    amount = Column(Numeric(12, 2), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    payment = relationship("Payment", back_populates="adjustments")

    __table_args__ = (
        Index("ix_payment_adjustment_carc", "carc_code"),
    )
