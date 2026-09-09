# backend/app/billing/models/readiness_assignment.py
"""
Generic, reusable assignment model (Sprint 2 -- Billing Readiness
Operational Workflow, Deliverable 4: Generic Assignment Framework).

Deliberately NOT a "biller" or "agency" specific concept -- `assigned_role`
is a free-form string column so this can be reused for any future
operational workflow that needs "who owns this right now", not just
billing readiness triage. No production onboarding/provisioning logic is
implied or required; this is development-phase scaffolding intended to be
driven by test/dev fixtures.

Every status transition is written to `readiness_workflow_events`
(entity_type='ASSIGNMENT') by
app.billing.services.readiness_workflow_service -- this table itself only
holds current state, never history.
"""

from __future__ import annotations

from sqlalchemy import Column, Date, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import BaseModel

ASSIGNMENT_STATUSES = {
    "UNASSIGNED",
    "ASSIGNED",
    "IN_PROGRESS",
    "COMPLETED",
    "REASSIGNED",
    "CANCELLED",
}


class ReadinessAssignment(BaseModel):
    __tablename__ = "readiness_assignments"

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

    assigned_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    # Free-form -- deliberately not an enum of real-world job titles.
    assigned_role = Column(String(64), nullable=True)

    assigned_date = Column(Date, nullable=True)

    assigned_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    assignment_status = Column(
        String(16), nullable=False, server_default="UNASSIGNED", index=True
    )

    __table_args__ = (
        Index("ix_readiness_assignments_tenant_patient", "tenant_id", "patient_id"),
        Index("ix_readiness_assignments_status", "assignment_status"),
    )
