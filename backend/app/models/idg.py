from sqlalchemy import Column, Date, Text, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel

REQUIRED_IDG_DISCIPLINES = {"RN", "MD", "MSW", "SC"}


class IDGReview(BaseModel):
    __tablename__ = "idg_reviews"

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

    review_date = Column(Date, nullable=False)

    summary = Column(Text, nullable=False)

    poc_action = Column(
        Enum("CONTINUED", "UPDATED", "ESCALATED", name="idg_poc_action"),
        nullable=False,
    )

    signatures = relationship(
        "IDGSignature",
        back_populates="idg_review",
        cascade="all, delete-orphan",
    )

    # ✅ PURE HELPER — SAFE IN MODEL
    def missing_required_signatures(self) -> set[str]:
        signed = {sig.discipline for sig in self.signatures}
        return REQUIRED_IDG_DISCIPLINES - signed
