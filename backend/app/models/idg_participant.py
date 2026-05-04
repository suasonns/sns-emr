from sqlalchemy import Column, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel

class IDGParticipant(BaseModel):
    __tablename__ = "idg_participants"

    participant_id = Column(UUID(as_uuid=True), primary_key=True)
    idg_id = Column(UUID(as_uuid=True), ForeignKey("idg_meetings.idg_id"), nullable=False)

    discipline = Column(String(50), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    participation_status = Column(Enum("PRESENT","NOT_PRESENT","EXCUSED", name="idg_participation_status_enum", create_type=False), nullable=False)
    reason_if_excused = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True))