# backend/app/models/form_registry_model.py
from uuid import uuid4
from sqlalchemy import Boolean, Column, DateTime, String, func, Index
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base

class FormRegistryModel(Base):
    __tablename__ = "form_registry"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    form_type = Column(String(64), nullable=False, index=True)
    form_family = Column(String(64), nullable=False, index=True)
    discipline = Column(String(32), nullable=False, index=True)
    level_of_care = Column(String(32), nullable=True, index=True)
    form_key = Column(String(128), nullable=False, unique=True, index=True)
    is_primary = Column(Boolean, nullable=False, default=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        Index(
            "ix_form_registry_resolution",
            "discipline",
            "form_type",
            "level_of_care",
        ),
    )
