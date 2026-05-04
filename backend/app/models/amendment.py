from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from app.models.base import BaseModel


class Amendment(BaseModel):
    __tablename__ = "amendments"

    clinical_note_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clinical_notes.id"),
        nullable=False,
    )

    author_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )

    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )

    reason = Column(String, nullable=False)
    content = Column(Text, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    # ✅ REQUIRED for compliance + your API
    original_finalized_at = Column(DateTime, nullable=True)