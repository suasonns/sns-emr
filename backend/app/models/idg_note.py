from sqlalchemy import Column, DateTime, ForeignKey, String, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel

class IDGNote(BaseModel):
    __tablename__ = "idg_notes"

    idg_note_id = Column(UUID(as_uuid=True), primary_key=True)
    idg_id = Column(UUID(as_uuid=True), ForeignKey("idg_meetings.idg_id"), nullable=False)

    discipline = Column(String(50), nullable=False)
    author_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    summary = Column(Text, nullable=False)
    recommendations = Column(Text, nullable=True)
    change_in_condition = Column(Boolean, nullable=False)
    poc_change_recommended = Column(Boolean, nullable=False)

    signed_at = Column(DateTime(timezone=True), nullable=False)