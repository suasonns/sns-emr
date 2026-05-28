from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.sql import func

from app.models.base import BaseModel


class EligibilityDecision(BaseModel):
    """
    Immutable eligibility determination record.

    Compliance relevance:
    - LCD/MAC traceability
    - Decision timing evidence
    - Config hash reproducibility
    """

    __tablename__ = "eligibility_decisions"

    # ---------------------------------------------------------
    # Identity
    # ---------------------------------------------------------
    id = Column(Integer, primary_key=True)

    # ---------------------------------------------------------
    # Relationships
    # ---------------------------------------------------------
    patient_id = Column(
        Integer,
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ---------------------------------------------------------
    # Decision metadata
    # ---------------------------------------------------------
    decision = Column(String(50), nullable=False)

    lcd_id = Column(String(20), nullable=False)
    mac = Column(String(20), nullable=False)
    mac_type = Column(String(10), nullable=False)

    lcd_effective_date = Column(Date, nullable=False)

    # ---------------------------------------------------------
    # Timing / integrity
    # ---------------------------------------------------------
    decision_timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Hash of ruleset / config used to produce the decision
    config_hash = Column(String(64), nullable=False)

    # ---------------------------------------------------------
    # Indexes (compliance + performance)
    # ---------------------------------------------------------
    __table_args__ = (
        Index(
            "ix_eligibility_decisions_patient_decision_time",
            "patient_id",
            "decision_timestamp",
        ),
    )