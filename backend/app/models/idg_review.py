"""
Enterprise-grade Interdisciplinary Group (IDG) Review model.

Canonical CMS CoPs §418.56 record.
This file MUST contain only the official IDG review entity.
"""

from datetime import date
from typing import Set

from sqlalchemy import Boolean, Column, Date, DateTime, Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import BaseModel


# ---------------------------------------------------------------------
# Required disciplines per CMS CoPs
# ---------------------------------------------------------------------
REQUIRED_IDG_DISCIPLINES: Set[str] = {"RN", "MD", "MSW", "SC"}


class IDGReview(BaseModel):
    __tablename__ = "idg_reviews"

    # -----------------------------------------------------------------
    # Core anchors
    # -----------------------------------------------------------------
    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id"),
        nullable=False,
    )

    benefit_period_id = Column(
        UUID(as_uuid=True),
        ForeignKey("benefit_periods.id"),
        nullable=True,
    )

    review_date = Column(
        Date,
        nullable=False,
    )

    # -----------------------------------------------------------------
    # Clinical summary
    # -----------------------------------------------------------------
    summary = Column(
        Text,
        nullable=False,
    )

    poc_action = Column(
        Enum(
            "CONTINUED",
            "UPDATED",
            "ESCALATED",
            name="idg_poc_action",
            create_type=False,
        ),
        nullable=False,
    )

    # -----------------------------------------------------------------
    # Governance / audit controls
    # -----------------------------------------------------------------
    is_finalized = Column(
        Boolean,
        nullable=False,
        server_default="false",
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    created_by = Column(
        Text,
        nullable=True,
    )

    finalized_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    finalized_by = Column(
        Text,
        nullable=True,
    )

    # -----------------------------------------------------------------
    # Relationships
    # -----------------------------------------------------------------
    signatures = relationship(
        "IDGSignature",
        back_populates="idg_review",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # -----------------------------------------------------------------
    # Pure helpers (SAFE)
    # -----------------------------------------------------------------
    def missing_required_signatures(self) -> Set[str]:
        """
        Returns the set of required disciplines that have not signed.
        """
        if not self.signatures:
            return REQUIRED_IDG_DISCIPLINES.copy()

        signed = {sig.discipline for sig in self.signatures}
        return REQUIRED_IDG_DISCIPLINES - signed