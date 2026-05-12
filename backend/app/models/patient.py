from sqlalchemy import Column, String, Date, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import BaseModel


class Patient(BaseModel):
    __tablename__ = "patients"

    # ✅ MULTI-TENANT OWNERSHIP (MUST BE INSIDE CLASS)
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )

    mrn = Column(String, unique=True, nullable=False)
    full_name = Column(String, nullable=False)
    date_of_birth = Column(Date, nullable=False)
    primary_diagnosis = Column(String, nullable=False)
    status = Column(String, nullable=False)

    hospice_election_date = Column(Date, nullable=True)
    discharge_date = Column(Date, nullable=True)
    discharge_reason = Column(String, nullable=True)

    # ✅ Crisis / acuity tracking
    acuity_state = Column(String, nullable=False, default="ROUTINE")
    crisis_started_at = Column(DateTime, nullable=True)
    crisis_ended_at = Column(DateTime, nullable=True)