from sqlalchemy import Column, String, Text, DateTime, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from app.models.base import BaseModel

class CHHAPOC(BaseModel):
    __tablename__ = "chha_pocs"

    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)

    status = Column(String, nullable=False, default="draft")

    effective_start = Column(Date, nullable=True)
    effective_end = Column(Date, nullable=True)

    frequency = Column(String, nullable=True)
    adl_scope = Column(Text, nullable=True)
    instructions = Column(Text, nullable=True)
    safety_precautions = Column(Text, nullable=True)

    finalized_at = Column(DateTime, nullable=True)
    finalized_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    def finalize(self, *, finalized_by):
        if self.finalized_at is not None:
            raise ValueError("CHHA POC already finalized")
        self.status = "active"
        self.finalized_at = datetime.utcnow()
        self.finalized_by = finalized_by