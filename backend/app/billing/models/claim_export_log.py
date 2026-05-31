from sqlalchemy import Column, String, DateTime, Boolean
from datetime import datetime

from app.db.base import Base


class ClaimExportLog(Base):
    __tablename__ = "claim_export_log"

    id = Column(String, primary_key=True)

    patient_id = Column(String, nullable=False)
    billing_cycle_id = Column(String, nullable=False)

    file_path = Column(String, nullable=False)

    # ✅ NEW FIELDS (OVERRIDE SYSTEM)
    override_used = Column(Boolean, default=False)
    override_reason = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)