# backend/app/billing/models/readiness_follow_up.py
"""
Generic follow-up / workflow tracking (Sprint 2 -- Billing Readiness
Operational Workflow, Deliverable 5). Not agency-specific -- reusable for
any operational item that needs a due date and a resolution trail.

`status` includes BLOCKED specifically because the Operational Queue's
"Blocked" bucket (Deliverable 1/7) is derived from this field, not from
the system-computed readiness status (see
app.billing.services.readiness_workflow_service.derive_readiness_status
and docs/planning/eligibility_traceability_epic.md, Sprint 2 design
note) -- a NOT_READY patient only counts as "Blocked" on the dashboard
when staff has explicitly set an open follow-up to BLOCKED.
"""

from __future__ import annotations

from sqlalchemy import Boolean, Column, Date, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.models.base import BaseModel

FOLLOW_UP_STATUSES = {"OPEN", "IN_PROGRESS", "BLOCKED", "RESOLVED", "CANCELLED"}


class ReadinessFollowUp(BaseModel):
    __tablename__ = "readiness_follow_ups"

    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id"),
        nullable=False,
        index=True,
    )

    assignment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("readiness_assignments.id"),
        nullable=True,
        index=True,
    )

    follow_up_required = Column(Boolean, nullable=False, server_default="true")

    # OPEN | IN_PROGRESS | BLOCKED | RESOLVED | CANCELLED
    status = Column(String(16), nullable=False, server_default="OPEN", index=True)

    due_date = Column(Date, nullable=True)
    resolved_date = Column(Date, nullable=True)
    created_date = Column(Date, nullable=False, server_default=func.current_date())

    notes = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_readiness_follow_ups_tenant_status", "tenant_id", "status"),
        Index("ix_readiness_follow_ups_patient_status", "patient_id", "status"),
        Index("ix_readiness_follow_ups_due_date", "due_date"),
    )
