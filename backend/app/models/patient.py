from sqlalchemy import Column, String, Date, DateTime, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import BaseModel
from app.models.tenant_mixin import TenantScopedMixin


class Patient(TenantScopedMixin, BaseModel):
    __tablename__ = "patients"

    # ---------------------------------------------------------
    # Tenant isolation
    # ---------------------------------------------------------
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )

    # ---------------------------------------------------------
    # Core identity
    # ---------------------------------------------------------
    mrn = Column(String, unique=True, nullable=False)
    full_name = Column(String, nullable=False)
    date_of_birth = Column(Date, nullable=False)
    primary_diagnosis = Column(String, nullable=False)

    # ---------------------------------------------------------
    # Lifecycle state (DB + ORM aligned)
    # ---------------------------------------------------------
    status = Column(
        String,
        nullable=False,
        server_default=text("'ACTIVE'"),
    )

    # ---------------------------------------------------------
    # Hospice lifecycle
    # ---------------------------------------------------------
    hospice_election_date = Column(Date, nullable=True)
    discharge_date = Column(Date, nullable=True)
    discharge_reason = Column(String, nullable=True)

    # ---------------------------------------------------------
    # Clinical acuity
    # ---------------------------------------------------------
    acuity_state = Column(
        String,
        nullable=False,
        server_default=text("'ROUTINE'"),
    )

    crisis_started_at = Column(DateTime, nullable=True)
    crisis_ended_at = Column(DateTime, nullable=True)

    # ---------------------------------------------------------
    # Audit provenance
    # ---------------------------------------------------------
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,   # will tighten after backfill
        index=True,
    )