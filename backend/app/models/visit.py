from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime

from app.models.base import BaseModel
from app.models.tenant import Tenant  # noqa: F401
from app.models.role import Role  # noqa: F401
from app.models.interface import Interface  # noqa: F401


class Visit(BaseModel):
    __tablename__ = "visits"

    # ✅ MULTI-TENANT OWNERSHIP
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )

    # ------------------------------------
    # Core relationships
    # ------------------------------------
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # ------------------------------------
    # Visit semantics (EXPLICIT)
    # ------------------------------------
    # ✅ SERVICE: what was delivered (SN, SW, CHAPLAIN, CHHA)
    visit_type = Column(String, nullable=False)

    # ✅ DISCIPLINE: who delivered it (RN, LVN, NP, MD)
    visit_discipline = Column(String, nullable=False)

    visit_datetime = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    status = Column(String, default="draft", nullable=False)

    # ------------------------------------
    # Clinical context snapshot (AUDIT-CRITICAL)
    # ------------------------------------
    acuity_state_at_visit = Column(String(32), nullable=True)

    # ------------------------------------
    # RN supervisory flag
    # ------------------------------------
    is_supervisory = Column(Boolean, nullable=False, default=False)

    # ------------------------------------
    # Finalization audit fields (LEGAL SNAPSHOT)
    # ------------------------------------
    finalized_at = Column(DateTime(timezone=True), nullable=True)

    finalized_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )

    finalized_role_id = Column(
        UUID(as_uuid=True),
        ForeignKey("roles.id"),
        nullable=True,
    )

    finalized_interface_id = Column(
        UUID(as_uuid=True),
        ForeignKey("interfaces.id"),
        nullable=True,
    )

    def finalize(self, *, finalized_by: UUID):
        if self.finalized_at is not None:
            raise ValueError("Visit already finalized")

        self.status = "finalized"
        self.finalized_at = datetime.utcnow()
        self.finalized_by = finalized_by