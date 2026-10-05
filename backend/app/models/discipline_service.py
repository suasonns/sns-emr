from __future__ import annotations

"""
Interdisciplinary continuity workflow (MSW / CHAPLAIN / VOLUNTEER ONLY).

Owner-authorized scope: MSW, CHAPLAIN, VOLUNTEER. RN/MD/F2F/Hospice-Aide
refusal pathways are explicitly OUT OF SCOPE and continue to use
app.models.refusal.Refusal / app.services.refusal_engine unchanged -- do
not route them through this module.

Two tables:
    PatientDisciplineService -- current-state projection. Exactly one
        active row per (tenant_id, patient_id, discipline).
    PatientDisciplineServiceEvent -- append-only event history. Never
        updated or deleted; corrections are new CORRECTION_RECORDED rows
        referencing the event they correct via corrects_event_id.

All state transitions MUST go through
app.services.discipline_service_engine.DisciplineServiceEngine -- never
assign PatientDisciplineService.current_state directly.

RECORDED_BY / INFORMATION_SOURCE / DECISION_MAKER are intentionally three
separate, independently stored concepts on each event (owner directive):
    recorded_by_user_id   -- the authenticated SNS user entering the record.
    information_source    -- the person who provided the information.
    decision_maker_name /
    decision_maker_relationship -- the patient or authorized representative
        who actually made the decision. A Volunteer Coordinator (or any
        other recorder) may record a refusal but must never automatically
        become the decision-maker.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.models.base import BaseModel
from app.models.tenant_mixin import TenantScopedMixin


class PatientDisciplineService(TenantScopedMixin, BaseModel):
    """Current-state projection. current_state is a plain String (not a
    native Postgres enum) so new DisciplineServiceState values can be
    added additively without an ALTER TYPE migration -- validity is
    enforced in Python by DisciplineServiceEngine, matching the
    patient_issues.status / idg_reviews.follow_up_status convention
    already used elsewhere in this codebase."""

    __tablename__ = "patient_discipline_services"

    # id / created_at / created_by are inherited from BaseModel.
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)

    # Continuity episode-scoping. Nullable: legacy rows predating this
    # column cannot be deterministically attributed to an admission and
    # must remain historical/admission-unassigned -- never inferred from
    # patient_id, tenant_id, or the currently active admission. Immutable
    # after creation except through an explicit authorized correction.
    admission_id = Column(UUID(as_uuid=True), ForeignKey("admissions.id", ondelete="SET NULL"), nullable=True, index=True)

    discipline = Column(String(16), nullable=False, index=True)  # ContinuityDiscipline: MSW / CHAPLAIN / VOLUNTEER

    current_state = Column(String(40), nullable=False, server_default=text("'NOT_YET_OFFERED'"), index=True)

    # Projection pointer -- the event that produced the current_state.
    current_state_event_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patient_discipline_service_events.id", ondelete="SET NULL", use_alter=True, name="fk_pds_current_state_event"),
        nullable=True,
    )

    # Optimistic concurrency.
    row_version = Column(Integer, nullable=False, server_default=text("1"))

    # Last-known decision-maker/information-source context (mirrors the
    # most recent event's values; authoritative history lives on the
    # event rows, never only here).
    last_decision_maker_name = Column(String(255), nullable=True)
    last_decision_maker_relationship = Column(String(64), nullable=True)
    last_information_source = Column(String(255), nullable=True)

    last_offered_at = Column(DateTime(timezone=True), nullable=True)
    last_decision_at = Column(DateTime(timezone=True), nullable=True)
    last_refused_at = Column(DateTime(timezone=True), nullable=True)
    reoffer_due_at = Column(DateTime(timezone=True), nullable=True)

    rn_monitoring_assigned_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    idg_review_required = Column(
        "idg_review_required",
        Boolean,
        nullable=False,
        server_default=text("false"),
    )
    idg_review_id = Column(UUID(as_uuid=True), ForeignKey("idg_reviews.id", ondelete="SET NULL"), nullable=True)

    # Override BaseModel.updated_at (nullable there) to make it NOT NULL
    # with a server default, since this is a current-state projection row
    # that is always updated at creation time.
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=text("now()"),
    )

    __table_args__ = (
        # Admission-scoped uniqueness (replaces the pre-admission-scoping
        # uq_pds_tenant_patient_discipline constraint). admission_id is
        # nullable, and Postgres treats NULL as distinct in a unique
        # constraint, so legacy admission-unassigned rows are intentionally
        # NOT covered by this uniqueness guarantee -- they remain historical
        # and are never selected as the current/active row by
        # get_or_create_service().
        UniqueConstraint(
            "tenant_id", "patient_id", "admission_id", "discipline",
            name="uq_pds_tenant_patient_admission_discipline",
        ),
        Index("ix_pds_tenant_patient", "tenant_id", "patient_id"),
        Index("ix_pds_tenant_patient_admission", "tenant_id", "patient_id", "admission_id"),
        CheckConstraint(
            "discipline IN ('MSW','CHAPLAIN','VOLUNTEER')",
            name="ck_pds_discipline_in_scope",
        ),
    )


class PatientDisciplineServiceEvent(TenantScopedMixin, BaseModel):
    """Append-only event history. Never updated or deleted -- corrections
    are new rows (event_type=CORRECTION_RECORDED) referencing the event
    they correct via corrects_event_id.

    Admission attribution decision (readmission episode-scoping): this
    table intentionally has NO admission_id column of its own (Option B,
    parent-derived attribution) rather than duplicating one on every
    event (Option A). Every event is permanently attributable to exactly
    one admission (or explicitly admission-unassigned) via its immutable
    discipline_service_id -> PatientDisciplineService.admission_id. This
    is enforced by, not merely documented as, immutability:
      - discipline_service_id is never reassigned after insert (no code
        path updates it) -- events are never reparented.
      - PatientDisciplineService.admission_id is set once at creation by
        get_or_create_service() and is never reassigned afterward (no
        code path updates an existing service row's admission_id).
      - All history/timeline/audit queries join through
        discipline_service_id, so they naturally stay within one
        admission's events without an extra predicate.
      - ON DELETE for discipline_service_id is CASCADE (see FK below),
        so a service row can never be deleted while leaving orphaned
        events silently reattributed elsewhere.
    This matches the existing append-only/event-sourced audit convention
    in this table (corrections-as-new-rows) rather than introducing a
    second, redundant admission column that could drift from its parent.
    """

    __tablename__ = "patient_discipline_service_events"

    # id / created_by are inherited from BaseModel. created_at is
    # overridden below (indexed, no onupdate needed -- rows are never
    # updated).
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    discipline_service_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patient_discipline_services.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    event_type = Column(String(50), nullable=False, index=True)
    from_state = Column(String(40), nullable=True)
    to_state = Column(String(40), nullable=False)

    # --- Three distinct, independently stored concepts (owner directive) ---
    recorded_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    recorded_by_role = Column(String(32), nullable=True)
    information_source = Column(String(255), nullable=True)
    decision_maker_name = Column(String(255), nullable=True)
    decision_maker_relationship = Column(String(64), nullable=True)
    # ------------------------------------------------------------------

    reason = Column(Text, nullable=True)
    effective_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    related_task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True)
    related_idg_review_id = Column(UUID(as_uuid=True), ForeignKey("idg_reviews.id", ondelete="SET NULL"), nullable=True)
    related_patient_issue_id = Column(UUID(as_uuid=True), ForeignKey("patient_issues.id", ondelete="SET NULL"), nullable=True)

    corrects_event_id = Column(UUID(as_uuid=True), ForeignKey("patient_discipline_service_events.id"), nullable=True)
    correlation_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    idempotency_key = Column(String(128), nullable=True)

    event_metadata = Column("metadata", JSONB, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"), index=True)

    __table_args__ = (
        Index("ix_pdse_tenant_patient_created", "tenant_id", "patient_id", "created_at"),
        Index("ix_pdse_discipline_service_created", "discipline_service_id", "created_at"),
        UniqueConstraint("tenant_id", "idempotency_key", name="uq_pdse_tenant_idempotency_key"),
    )
