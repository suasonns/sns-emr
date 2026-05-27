from sqlalchemy import Column, String, DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import BaseModel
from app.models.tenant_mixin import TenantScopedMixin


class PatientAssignment(TenantScopedMixin, BaseModel):
    __tablename__ = "patient_assignments"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True)

    discipline = Column(String(16), nullable=False)  # RN/MSW/SC
    staff_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    service_area = Column(String(64), nullable=True)

    status = Column(String(16), nullable=False, server_default="ASSIGNED")
    assigned_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    assigned_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    note = Column(Text, nullable=True)
