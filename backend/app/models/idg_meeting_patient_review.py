# models/idg_meeting_patient_review.py

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class IDGMeetingPatientReview(Base):
    """
    The temporary workspace record created while a patient is being
    discussed DURING an IDG meeting.

    Domain model (per SNS Hospice Solutions IDG entity spec — "IDG" is
    overloaded and must NOT be modeled as one generic object):

        1. PatientIDGReview (see idg_review.py / IDGReview) — the
           patient-chart clinical documentation (Admission/Initial/
           Routine/Recert/Significant-Change IDG review notes). Belongs
           to ONE patient. This is NOT a meeting.

        2. IDGMeeting (see idg_meeting.py) — the recurring (~every 14
           days) scheduled interdisciplinary team meeting itself: date/
           time, attendees, agenda, minutes, status. This is NOT a
           patient note.

        3. IDGMeetingPatientReview (this table) — the in-meeting review
           workspace: tracks POC review, medication list review,
           medication reconciliation, pending-orders review, physician
           review status (Pending/Reviewed/Deferred), and defer
           workflow for ONE patient within ONE IDGMeeting. Determines
           batch-sign eligibility. This is NOT the meeting and NOT the
           patient's chart documentation — those are updated separately
           once this in-meeting review closes.

    Review vs. Signature are separate events:
        - Review happens during patient discussion (review_status,
          reviewed_at, physician_user_id / recorded_by_user_id,
          defer_reason, reviewed-item checklist).
        - Signature happens after IDG, when the physician logs in and
          batch-signs (see physician_order_service.approve_order —
          signed_at/order_id live on PhysicianOrder, not here).
    """

    __tablename__ = "idg_meeting_patient_reviews"

    __table_args__ = (
        UniqueConstraint(
            "idg_meeting_id",
            "patient_id",
            name="uq_idg_meeting_patient_review_session_patient",
        ),
        Index("ix_idg_mpr_tenant_id", "tenant_id"),
        Index("ix_idg_mpr_patient_id", "patient_id"),
        Index("ix_idg_mpr_idg_meeting_id", "idg_meeting_id"),
        Index("ix_idg_mpr_physician_user_id", "physician_user_id"),
        Index("ix_idg_mpr_review_status", "review_status"),
        Index("ix_idg_mpr_recorded_by_user_id", "recorded_by_user_id"),
    )

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    tenant_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    patient_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    # The IDG meeting this in-meeting review is scoped to.
    idg_meeting_id = Column(
        UUID(as_uuid=True),
        ForeignKey("idg_meetings.id"),
        nullable=False,
        index=True,
    )

    physician_user_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    # Who actually clicked the review button. May differ from
    # physician_user_id: if the facilitator/RN recorded the review while
    # the physician verbally participated in IDG, this is the RN/MSW/etc.
    # who performed the click — NOT falsely attributed to the physician.
    recorded_by_user_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    # Set only when the physician personally authenticated and clicked
    # the review action themselves (e.g. logged into the system during
    # or after IDG). Distinguishes a true physician click from a
    # facilitator-recorded review.
    reviewed_by_physician_directly = Column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )

    # Where this review was captured — always IDG today, but keeps the
    # door open for a later post-IDG chart-review workflow.
    review_source = Column(
        String(30),
        nullable=False,
        server_default=text("'IDG'"),
    )

    # PENDING | REVIEWED | DEFERRED
    review_status = Column(
        String(20),
        nullable=False,
        server_default=text("'PENDING'"),
        index=True,
    )

    # Reason dropdown shown only when review_status = DEFERRED.
    defer_reason = Column(
        String(100),
        nullable=True,
    )

    defer_note = Column(
        Text,
        nullable=True,
    )

    # Review Timestamp — when the physician marked this patient
    # Reviewed/Deferred (updated on every status change).
    reviewed_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    notes = Column(
        Text,
        nullable=True,
    )

    # Reviewed-item checklist — what was actually covered during the
    # IDG discussion for this patient before marking Reviewed.
    poc_reviewed = Column(Boolean, nullable=False, server_default=text("false"))
    medication_list_reviewed = Column(Boolean, nullable=False, server_default=text("false"))
    medication_reconciliation_reviewed = Column(Boolean, nullable=False, server_default=text("false"))
    orders_reviewed = Column(Boolean, nullable=False, server_default=text("false"))
    discussion_reviewed = Column(Boolean, nullable=False, server_default=text("false"))

    # Batch-sign bookkeeping — separate from review status (rule 8:
    # review status and signature status are distinct workflow states).
    batch_signed_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        onupdate=datetime.utcnow,
    )
