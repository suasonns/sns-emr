"""
Enterprise-grade MD attestation for IDG review.

Regulatory basis:
- CMS CoPs §418.56(c)(1)
"""

from sqlalchemy import Column, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.models.base import BaseModel


class IDGMDAttestation(BaseModel):
    __tablename__ = "idg_md_attestations"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
    )

    idg_review_id = Column(
        UUID(as_uuid=True),
        ForeignKey("idg_reviews.id", ondelete="CASCADE"),
        nullable=False,
    )

    md_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )

    attestation_text = Column(
        Text,
        nullable=False,
    )

    signed_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )