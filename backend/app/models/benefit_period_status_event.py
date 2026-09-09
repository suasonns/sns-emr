# backend/app/models/benefit_period_status_event.py
"""
Immutable, append-only audit trail of every BenefitPeriod lifecycle action
(created, rolled, closed, corrected, reopened).

Closes the confirmed Audit Gap documented across this engagement's review
phases (see docs/planning/benefit_period_audit_design.md and
docs/planning/eligibility_traceability_epic.md, Workstream 1): unlike
CertificationStatusEvent / AdmissionStatusHistory, BenefitPeriod previously
had no event history and no enforced actor attribution
(BenefitPeriod.created_by existed but was never populated).

Design intentionally mirrors CertificationStatusEvent / AdmissionStatusHistory:
append-only, no update/delete path, actor attribution enforced at the schema
level (actor_user_id is NOT NULL) rather than relying on application-layer
convention alone.

`related_certification_id` is populated only when a certification check is
known to have gated the event (Workstream 6 -- Certification -> BenefitPeriod
linkage -- which is deferred pending product review of hard-gate vs.
soft-record behavior). It is nullable and unpopulated by this workstream's
code; adding that population is explicitly out of scope until that review
happens.
"""

from __future__ import annotations

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from app.models.base import BaseModel


class BenefitPeriodStatusEvent(BaseModel):
    __tablename__ = "benefit_period_status_events"

    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    benefit_period_id = Column(
        UUID(as_uuid=True),
        ForeignKey("benefit_periods.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # CREATED | ROLLED | CLOSED | CORRECTED | REOPENED
    event_type = Column(String(32), nullable=False, index=True)

    # Enforced NOT NULL at the schema level -- no event can be written
    # without a real actor, closing the Attribution Gap for this table.
    actor_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    occurred_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    # Required (app-layer) for CORRECTED/REOPENED; optional for
    # CREATED/ROLLED, matching the CertificationStatusEvent.reason pattern.
    reason = Column(Text, nullable=True)

    # Row-state snapshots -- null previous_value only on CREATED.
    previous_value = Column(JSONB, nullable=True)
    new_value = Column(JSONB, nullable=False)

    # Forward causal link to the certification that authorized this event,
    # if known. Nullable and unpopulated until Workstream 6 ships.
    related_certification_id = Column(
        UUID(as_uuid=True),
        ForeignKey("certifications.id"),
        nullable=True,
        index=True,
    )

    __table_args__ = (
        Index(
            "ix_bp_status_events_bp_time",
            "benefit_period_id",
            "occurred_at",
        ),
    )
