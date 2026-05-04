from sqlalchemy import Column, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class IDGSignature(BaseModel):
    __tablename__ = "idg_signatures"

    idg_review_id = Column(
        UUID(as_uuid=True),
        ForeignKey("idg_reviews.id", ondelete="CASCADE"),
        nullable=False,
    )

    discipline = Column(
        Enum("RN", "MD", "MSW", "SC", "LVN", "NP", name="idg_discipline"),
        nullable=False,
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )

    signed_at = Column(DateTime, nullable=False)

    idg_review = relationship(
        "IDGReview",
        back_populates="signatures",
    )