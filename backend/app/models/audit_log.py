from sqlalchemy import Column, String, DateTime
from app.models.base import BaseModel
from datetime import datetime


class AuditLog(BaseModel):
    __tablename__ = "audit_logs"

    user_id = Column(String, nullable=False)
    role = Column(String, nullable=False)
    action = Column(String, nullable=False)
    entity_type = Column(String, nullable=True)
    entity_id = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
