# backend/app/models/form_package_module.py
from uuid import uuid4
from sqlalchemy import Column, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base

class FormPackageModule(Base):
    __tablename__ = "form_package_modules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    form_registry_id = Column(UUID(as_uuid=True), ForeignKey("form_registry.id", ondelete="CASCADE"), nullable=False, index=True)
    module_id = Column(UUID(as_uuid=True), ForeignKey("form_modules.id", ondelete="CASCADE"), nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint("form_registry_id", "module_id", name="uq_form_package_modules_registry_module"),
    )