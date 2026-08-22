from __future__ import annotations

from sqlalchemy import Column, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.models.base import BaseModel


# Request types tracked by the Admission Action Center (Phase A).
ADMISSION_ACTION_REQUEST_TYPES = (
    "MEDICATION_REQUEST",
    "PHYSICIAN_ORDER",
    "DME_ORDER",
    "SUPPLY_ORDER",
    "REFERRAL",
)

# Lifecycle statuses tracked by the Admission Action Center (Phase A).
# Deliberately simple: no approval gating, no fulfillment sub-states.
ADMISSION_ACTION_REQUEST_STATUSES = (
    "REQUESTED",
    "ORDERED",
    "SENT",
    "ACKNOWLEDGED",
    "DELIVERED",
    "COMPLETED",
)


class AdmissionActionRequest(BaseModel):
    """Admission Action Center (Phase A) request tracker.

    A lightweight, dedicated request/status tracker raised from any RN ICA
    section without leaving the assessment. This is intentionally NOT the
    same model as `PhysicianOrder` (MD-approval-gated) or `PatientOrder`
    (fulfillment-status DME/Supply/Lab/Treatment orders) -- Phase A tracks a
    simple linear status (REQUESTED -> ... -> COMPLETED) with no approval
    routing, no fulfillment workflow, and no notifications.
    """

    __tablename__ = "admission_action_requests"

    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Traceability: which RN ICA assessment / section this was raised from.
    # Nullable so the tracker is not hard-coupled to RNICA if reused later.
    rnica_assessment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("rnica_assessments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    source_section = Column(String(64), nullable=True)

    # MEDICATION_REQUEST | PHYSICIAN_ORDER | DME_ORDER | SUPPLY_ORDER | REFERRAL
    request_type = Column(String(32), nullable=False, index=True)

    # REQUESTED | ORDERED | SENT | ACKNOWLEDGED | DELIVERED | COMPLETED
    status = Column(String(32), nullable=False, server_default="REQUESTED", index=True)

    details = Column(Text, nullable=False)

    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Append-only status change log: [{"status": ..., "changed_by": ...,
    # "changed_at": ..., "note": ...}, ...]. Mirrors the Section 11.C
    # `evidence_sources` pattern -- traceability without a separate table.
    status_history = Column(JSONB, nullable=False, server_default="[]")

    __table_args__ = (
        Index("ix_admission_action_requests_patient_status", "patient_id", "status"),
        Index("ix_admission_action_requests_patient_type", "patient_id", "request_type"),
    )
