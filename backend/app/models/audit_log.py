from sqlalchemy import Column, String, DateTime
from datetime import datetime

from app.models.base import BaseModel


class AuditLog(BaseModel):
    __tablename__ = "audit_logs"

    # ------------------------------------------------------------------
    # REQUEST CONTEXT (NEW - REQUIRED FOR TRACEABILITY)
    # ------------------------------------------------------------------
    request_id = Column(String, nullable=True)
    tenant_id = Column(String, nullable=True)

    # ------------------------------------------------------------------
    # ACTOR CONTEXT
    # ------------------------------------------------------------------
    user_id = Column(String, nullable=True)   # allow SYSTEM / anonymous
    role = Column(String, nullable=True)

    # ------------------------------------------------------------------
    # EVENT DETAILS
    # ------------------------------------------------------------------
    action = Column(String, nullable=False)
    entity_type = Column(String, nullable=True)
    entity_id = Column(String, nullable=True)

    # ------------------------------------------------------------------
    # NETWORK CONTEXT
    # ------------------------------------------------------------------
    ip_address = Column(String, nullable=True)

    # ------------------------------------------------------------------
    # TIMESTAMP
    # ------------------------------------------------------------------
    created_at = Column(DateTime, default=datetime.utcnow)
