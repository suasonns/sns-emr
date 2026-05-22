from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import BaseModel


class DxPrimaryPolicy(BaseModel):
    """
    Governs allowed / disallowed primary hospice diagnoses.
    Used by dx_policy service to enforce CMS-aligned diagnosis integrity.
    """

    __tablename__ = "dx_primary_policies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # e.g. "COPD", "CHF", "Cancer"
    diagnosis_code = Column(String(64), nullable=False, index=True)

    # Human-readable label
    diagnosis_name = Column(String(255), nullable=False)

    # Whether this diagnosis is allowed as PRIMARY hospice diagnosis
    allowed_primary = Column(Boolean, nullable=False, default=True)

    # Optional reason / governance note
    rationale = Column(String(512), nullable=True)

    active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)