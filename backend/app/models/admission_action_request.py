from __future__ import annotations

from sqlalchemy import Column, Date, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.models.base import BaseModel


# Request types tracked by the Admission Action Center (Phase A).
ADMISSION_ACTION_REQUEST_TYPES = (
    "MEDICATION_REQUEST",
    "PHYSICIAN_ORDER",
    "DME_ORDER",
    "SUPPLY_ORDER",
    "REFERRAL",
    "PHYSICIAN_CONTACT",
)

# Lifecycle statuses tracked by the Admission Action Center (Phase A).
# Deliberately simple: no approval gating, no fulfillment sub-states.
# CANCELED is a terminal status distinct from COMPLETED -- it requires an
# explicit `cancellation_reason` (enforced in the service layer) and never
# implies the underlying need was met.
ADMISSION_ACTION_REQUEST_STATUSES = (
    "REQUESTED",
    "ACKNOWLEDGED",
    "IN_PROGRESS",
    "ORDERED",
    "SENT",
    "DELIVERED",
    "COMPLETED",
    "CANCELED",
)

# Priorities available across all request types (mirrors
# app.services.physician_order_service.VALID_PRIORITIES).
ADMISSION_ACTION_REQUEST_PRIORITIES = ("ROUTINE", "URGENT", "STAT")


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

    # MEDICATION_REQUEST | PHYSICIAN_ORDER | DME_ORDER | SUPPLY_ORDER |
    # REFERRAL | PHYSICIAN_CONTACT
    request_type = Column(String(32), nullable=False, index=True)

    # REQUESTED | ACKNOWLEDGED | IN_PROGRESS | ORDERED | SENT | DELIVERED |
    # COMPLETED | CANCELED
    status = Column(String(32), nullable=False, server_default="REQUESTED", index=True)

    details = Column(Text, nullable=False)

    # Responsible discipline for fulfilling the request (e.g. "RN", "MSW",
    # "MD", "PHARMACY", "DME_VENDOR"). Free-text-constrained at the API/service
    # layer rather than a DB enum so new disciplines don't require a migration.
    responsible_discipline = Column(String(32), nullable=True)

    # ROUTINE | URGENT | STAT (see ADMISSION_ACTION_REQUEST_PRIORITIES).
    priority = Column(String(16), nullable=False, server_default="ROUTINE")

    required_by_date = Column(Date, nullable=True)

    # Type-specific structured fields (item/qty/vendor/delivery for DME &
    # Supply; destination/reason/transmitted/accepted/appointment/outcome for
    # Referral; physician/method/reason/attempted/reached/response/read-back
    # for Physician Contact). Kept as JSONB rather than ~20 dedicated columns
    # so each request_type's shape can evolve without a schema migration;
    # the service layer validates required keys per request_type.
    type_details = Column(JSONB, nullable=False, server_default="{}")

    # Optional linkage to the individualized plan of care (CDPH: POC must
    # identify medical supplies/equipment required for care).
    plan_of_care_version_id = Column(
        UUID(as_uuid=True),
        ForeignKey("plan_of_care_versions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Timestamped completion evidence is required before status can become
    # COMPLETED (enforced in the service layer) -- a checkbox alone is never
    # sufficient proof the request was fulfilled.
    completed_at = Column(DateTime(timezone=True), nullable=True)
    completion_evidence = Column(Text, nullable=True)

    # Required whenever status is set to CANCELED (enforced in service layer).
    cancellation_reason = Column(Text, nullable=True)

    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Append-only status change log: [{"status": ..., "changed_by": ...,
    # "changed_at": ..., "note": ...}, ...]. Mirrors the Section 11.C
    # `evidence_sources` pattern -- traceability without a separate table.
    status_history = Column(JSONB, nullable=False, server_default="[]")

    __table_args__ = (
        Index("ix_admission_action_requests_patient_status", "patient_id", "status"),
        Index("ix_admission_action_requests_patient_type", "patient_id", "request_type"),
    )
