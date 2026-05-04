from sqlalchemy import Column, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel

class IDGMDAttestation(BaseModel):
    __tablename__ = "idg_md_attestations"

    attestation_id = Column(UUID(as_uuid=True), primary_key=True)
    idg_id = Column(UUID(as_uuid=True), ForeignKey("idg_meetings.idg_id"), nullable=False)

    md_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    attestation_text = Column(Text, nullable=False)
    signed_at = Column(DateTime(timezone=True), nullable=False)