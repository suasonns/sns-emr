# backend/app/billing/models/readiness_workflow_event.py
"""
Single, shared audit trail for every Sprint 2 (Billing Readiness
Operational Workflow) state change -- blocker resolution, assignment
change, and follow-up status change (Deliverable 9: Audit Requirements).

Mirrors `app.models.benefit_period_status_event.BenefitPeriodStatusEvent`'s
proven append-only design exactly on purpose: enforced actor attribution
(actor_user_id NOT NULL), previous_value/new_value JSONB snapshots, and a
forward link back to the BillingReadinessVerdict that was current when
the change happened (`related_verdict_id`) -- this is a sibling table
alongside BenefitPeriodStatusEvent, not a competing/parallel audit
mechanism: Sprint 1's benefit-period lifecycle events stay in that table,
and every Sprint-2-introduced entity's lifecycle events land here.
"""

from __future__ import annotations

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from app.models.base import BaseModel

# BLOCKER | ASSIGNMENT | FOLLOW_UP
WORKFLOW_ENTITY_TYPES = {"BLOCKER", "ASSIGNMENT", "FOLLOW_UP"}


class ReadinessWorkflowEvent(BaseModel):
    __tablename__ = "readiness_workflow_events"

    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # BLOCKER | ASSIGNMENT | FOLLOW_UP
    entity_type = Column(String(16), nullable=False, index=True)

    # id of the billing_blocker_records / readiness_assignments /
    # readiness_follow_ups row this event describes.
    entity_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # e.g. CREATED | STATUS_CHANGED | REASSIGNED | RESOLVED | CANCELLED
    event_type = Column(String(32), nullable=False, index=True)

    # Nullable here (unlike BenefitPeriodStatusEvent's NOT NULL actor,
    # which only ever records human-driven lifecycle actions): a blocker
    # can be auto-resolved by the same unattended sync step that persists
    # a BillingReadinessVerdict for a SCHEDULED_CHECK, which has no
    # authenticated user in context. Every manually-driven event (created
    # via an API endpoint, which always requires get_current_user) MUST
    # populate this at the service-call layer -- enforced in
    # app.billing.services.readiness_workflow_service, not by the schema,
    # since there is no dedicated "system user" row to satisfy a NOT NULL
    # FK constraint for the auto-resolve case.
    actor_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    occurred_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )

    reason = Column(Text, nullable=True)

    previous_value = Column(JSONB, nullable=True)
    new_value = Column(JSONB, nullable=False)

    # Forward-traceability link to the readiness evaluation current at the
    # time of this change -- required by Deliverable 9 ("link to the
    # originating readiness evaluation"). Nullable only because a
    # follow-up/assignment can in principle be created before any
    # verdict has ever been recorded for a brand-new patient.
    related_verdict_id = Column(
        UUID(as_uuid=True), ForeignKey("billing_readiness_verdicts.id"), nullable=True, index=True
    )

    __table_args__ = (
        Index("ix_rwe_entity", "entity_type", "entity_id", "occurred_at"),
        Index("ix_rwe_tenant_occurred", "tenant_id", "occurred_at"),
    )
