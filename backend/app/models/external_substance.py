from __future__ import annotations

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel
from app.models.tenant_mixin import TenantScopedMixin


class ExternalSubstance(TenantScopedMixin, BaseModel):
    __tablename__ = "external_substances"

    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name = Column(
        String(255),
        nullable=False,
        index=True,
    )

    substance_type = Column(
        String(32),
        nullable=False,
        server_default=text("'UNKNOWN'"),
        index=True,
    )
    # HERBAL, SUPPLEMENT, OTC, FOOD_BASED, UNKNOWN

    initiated_by = Column(
        String(32),
        nullable=False,
        server_default=text("'FAMILY'"),
        index=True,
    )
    # FAMILY, PATIENT, CAREGIVER, OTHER

    ordered_by_provider = Column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )

    purpose = Column(
        Text,
        nullable=True,
    )

    known_interactions = Column(
        Text,
        nullable=True,
    )

    clinician_reviewed = Column(
        Boolean,
        nullable=False,
        server_default=text("false"),
        index=True,
    )

    clinician_action = Column(
        String(32),
        nullable=True,
        index=True,
    )
    # ALLOWED, DISCOURAGED, STOPPED, REFERRED_TO_MD

    clinician_notes = Column(
        Text,
        nullable=True,
    )

    coverage_intent = Column(
        String(32),
        nullable=False,
        server_default=text("'EXTERNAL'"),
        index=True,
    )

    financial_responsibility = Column(
        String(32),
        nullable=False,
        server_default=text("'PATIENT_FAMILY'"),
        index=True,
    )

    reviewed_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    reviewed_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    patient = relationship(
        "Patient",
        back_populates="external_substances",
    )
