from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime

from app.models.base import BaseModel


class Visit(BaseModel):
    __tablename__ = "visits"

    # ------------------------------------
    # Core relationships
    # ------------------------------------
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # RN-authored CHHA Plan of Care (separate from clinical POC)
    chha_poc_id = Column(UUID(as_uuid=True), ForeignKey("chha_pocs.id"), nullable=True)

    # ------------------------------------
    # Visit metadata
    # ------------------------------------
    visit_type = Column(String, nullable=False)  # RN, LVN, NP, MD, CHHA, etc.
    visit_datetime = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(String, default="draft", nullable=False)

    # ------------------------------------
    # Clinical context snapshot (AUDIT-CRITICAL)
    # ------------------------------------
    acuity_state_at_visit = Column(String(32), nullable=True)
    # Examples: ROUTINE, CRISIS

    # ------------------------------------
    # RN supervisory flag
    # ------------------------------------
    is_supervisory = Column(Boolean, nullable=False, default=False)

    # ------------------------------------
    # Finalization audit fields
    # ------------------------------------
    finalized_at = Column(DateTime, nullable=True)
    finalized_by = Column(UUID(as_uuid=True), nullable=True)

    # ------------------------------------
    # Domain behavior
    # ------------------------------------
    def finalize(self, *, finalized_by: UUID):
        if self.finalized_at is not None:
            raise ValueError("Visit already finalized")

        self.status = "finalized"
        self.finalized_at = datetime.utcnow()
        self.finalized_by = finalized_by
