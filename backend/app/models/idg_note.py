"""
Enterprise-grade IDG discipline note.

Purpose:
- Discipline-specific input supporting the canonical IDG review
- Anchored to idg_reviews per CMS CoPs §418.56
"""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.models.base import BaseModel


class IDGNote(BaseModel):
    __tablename__ = "idg_notes"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
    )

    idg_review_id = Column(
        UUID(as_uuid=True),
        ForeignKey("idg_reviews.id", ondelete="CASCADE"),
        nullable=False,
    )

    discipline = Column(
        String(50),
        nullable=False,
    )

    author_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )

    summary = Column(
        Text,
        nullable=False,
    )

    recommendations = Column(
        Text,
        nullable=True,
    )

    change_in_condition = Column(
        Boolean,
        nullable=False,
    )

    poc_change_recommended = Column(
        Boolean,
        nullable=False,
    )

    signed_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )