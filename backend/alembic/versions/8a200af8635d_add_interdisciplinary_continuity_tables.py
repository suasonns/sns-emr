"""interdisciplinary continuity workflow (MSW/CHAPLAIN/VOLUNTEER)

Owner-authorized scope: MSW, CHAPLAIN, VOLUNTEER discipline continuity
only. RN/MD/F2F/Hospice-Aide refusal pathways (app.models.refusal.Refusal)
are completely unmodified by this migration.

Adds:
  - new enum values: tasktype.VOLUNTEER_REOFFER, taskdiscipline.VOLUNTEER
  - patient_discipline_services (current-state projection)
  - patient_discipline_service_events (append-only event history)
  - idg_recommendations (MSW/CHAPLAIN recommendations without a visit,
    reusing the existing idg_reviews table as container)
  - additive columns on patient_issues

This migration is strictly additive: no existing column, table, or enum
value is modified or removed, and no backfill/inferred historical data is
written.

Admission episode-scoping (added before this migration was ever applied
to any persistent environment, so edited in place rather than chained):
patient_discipline_services and idg_recommendations each gain a nullable
admission_id FK to admissions.id, and the patient_discipline_services
uniqueness constraint is admission-scoped
(tenant_id, patient_id, admission_id, discipline) instead of
(tenant_id, patient_id, discipline). admission_id is nullable and never
backfilled/inferred -- legacy/admission-unassigned rows remain historical
and are excluded from current-admission lookup by application logic, not
by a NOT NULL constraint. idg_reviews.admission_id is NOT added here:
idg_reviews was created by the already-applied consolidated baseline
migration, so that column is added by a separate new migration.

Revision ID: 8a200af8635d
Revises: 7515a748100d
Create Date: 2026-09-29
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "8a200af8635d"
down_revision: Union[str, Sequence[str], None] = "7515a748100d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ALTER TYPE ... ADD VALUE cannot run inside the same transaction that
    # uses the new value -- run it in its own auto-committed statement
    # ahead of the rest of this migration (see b2c3d4e5f6a7 precedent).
    op.execute("COMMIT")
    op.execute("ALTER TYPE taskdiscipline ADD VALUE IF NOT EXISTS 'VOLUNTEER'")
    op.execute("ALTER TYPE tasktype ADD VALUE IF NOT EXISTS 'VOLUNTEER_REOFFER'")
    op.execute("BEGIN")

    # ---------------------------------------------------------------
    # patient_discipline_services -- current-state projection.
    # current_state/discipline are plain strings (not native Postgres
    # enums) so future state/discipline growth is additive without a
    # further ALTER TYPE migration; validity is enforced in Python by
    # DisciplineServiceEngine, matching the patient_issues.status /
    # idg_reviews.follow_up_status convention already used in this
    # codebase.
    # ---------------------------------------------------------------
    op.create_table(
        "patient_discipline_services",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        # Nullable: no historical row exists yet (table is new), but kept
        # nullable to match the same legacy/admission-unassigned convention
        # used everywhere else in this migration -- never backfilled/
        # inferred, only ever set at creation time by the engine.
        sa.Column("admission_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("discipline", sa.String(length=16), nullable=False),
        sa.Column("current_state", sa.String(length=40), nullable=False, server_default=sa.text("'NOT_YET_OFFERED'")),
        sa.Column("current_state_event_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("row_version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("last_decision_maker_name", sa.String(length=255), nullable=True),
        sa.Column("last_decision_maker_relationship", sa.String(length=64), nullable=True),
        sa.Column("last_information_source", sa.String(length=255), nullable=True),
        sa.Column("last_offered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_decision_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_refused_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reoffer_due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rn_monitoring_assigned_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("idg_review_required", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("idg_review_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["admission_id"], ["admissions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["rn_monitoring_assigned_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["idg_review_id"], ["idg_reviews.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id", "patient_id", "admission_id", "discipline",
            name="uq_pds_tenant_patient_admission_discipline",
        ),
        sa.CheckConstraint(
            "discipline IN ('MSW','CHAPLAIN','VOLUNTEER')",
            name="ck_pds_discipline_in_scope",
        ),
    )
    op.create_index("ix_patient_discipline_services_tenant_id", "patient_discipline_services", ["tenant_id"], unique=False)
    op.create_index("ix_patient_discipline_services_patient_id", "patient_discipline_services", ["patient_id"], unique=False)
    op.create_index("ix_patient_discipline_services_admission_id", "patient_discipline_services", ["admission_id"], unique=False)
    op.create_index("ix_patient_discipline_services_discipline", "patient_discipline_services", ["discipline"], unique=False)
    op.create_index("ix_patient_discipline_services_current_state", "patient_discipline_services", ["current_state"], unique=False)
    op.create_index("ix_pds_tenant_patient", "patient_discipline_services", ["tenant_id", "patient_id"], unique=False)
    op.create_index("ix_pds_tenant_patient_admission", "patient_discipline_services", ["tenant_id", "patient_id", "admission_id"], unique=False)
    op.create_index("ix_patient_discipline_services_created_by", "patient_discipline_services", ["created_by"], unique=False)

    # ---------------------------------------------------------------
    # patient_discipline_service_events -- append-only event history.
    # Never updated or deleted; corrections are new rows referencing the
    # event they correct via corrects_event_id.
    # ---------------------------------------------------------------
    op.create_table(
        "patient_discipline_service_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("discipline_service_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("from_state", sa.String(length=40), nullable=True),
        sa.Column("to_state", sa.String(length=40), nullable=False),
        sa.Column("recorded_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("recorded_by_role", sa.String(length=32), nullable=True),
        sa.Column("information_source", sa.String(length=255), nullable=True),
        sa.Column("decision_maker_name", sa.String(length=255), nullable=True),
        sa.Column("decision_maker_relationship", sa.String(length=64), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("effective_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("related_task_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("related_idg_review_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("related_patient_issue_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("corrects_event_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("correlation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("idempotency_key", sa.String(length=128), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["discipline_service_id"], ["patient_discipline_services.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recorded_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["related_task_id"], ["tasks.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["related_idg_review_id"], ["idg_reviews.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["related_patient_issue_id"], ["patient_issues.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["corrects_event_id"], ["patient_discipline_service_events.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "idempotency_key", name="uq_pdse_tenant_idempotency_key"),
    )
    op.create_index("ix_pdse_tenant_patient_created", "patient_discipline_service_events", ["tenant_id", "patient_id", "created_at"], unique=False)
    op.create_index("ix_pdse_discipline_service_created", "patient_discipline_service_events", ["discipline_service_id", "created_at"], unique=False)
    op.create_index("ix_patient_discipline_service_events_tenant_id", "patient_discipline_service_events", ["tenant_id"], unique=False)
    op.create_index("ix_patient_discipline_service_events_patient_id", "patient_discipline_service_events", ["patient_id"], unique=False)
    op.create_index("ix_patient_discipline_service_events_discipline_service_id", "patient_discipline_service_events", ["discipline_service_id"], unique=False)
    op.create_index("ix_patient_discipline_service_events_event_type", "patient_discipline_service_events", ["event_type"], unique=False)
    op.create_index("ix_patient_discipline_service_events_correlation_id", "patient_discipline_service_events", ["correlation_id"], unique=False)
    op.create_index("ix_patient_discipline_service_events_created_at", "patient_discipline_service_events", ["created_at"], unique=False)
    op.create_index("ix_patient_discipline_service_events_created_by", "patient_discipline_service_events", ["created_by"], unique=False)

    # Deferred FK: patient_discipline_services.current_state_event_id ->
    # patient_discipline_service_events.id (added after both tables exist,
    # matching the model's use_alter=True declaration).
    op.create_foreign_key(
        "fk_pds_current_state_event",
        "patient_discipline_services",
        "patient_discipline_service_events",
        ["current_state_event_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # ---------------------------------------------------------------
    # idg_recommendations -- reuses idg_reviews as container (owner
    # directive: do not create a second IDG review table).
    # ---------------------------------------------------------------
    op.create_table(
        "idg_recommendations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("admission_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("idg_review_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("discipline_service_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("discipline", sa.String(length=16), nullable=True),
        sa.Column("recommendation_type", sa.String(length=32), nullable=False),
        sa.Column("recommendation_text", sa.Text(), nullable=False),
        sa.Column("no_direct_visit", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("status", sa.String(length=16), nullable=False, server_default=sa.text("'PENDING'")),
        sa.Column("related_patient_issue_id", postgresql.UUID(as_uuid=True), nullable=True),
        # True Plan-of-Care linkage (owner directive: reuse existing
        # POCProblem/POCGoal/POCIntervention tables -- no second POC
        # system). Independently nullable: a recommendation may link
        # zero, one, or more of these; never fabricated/inferred, only
        # ever set at creation time from a client-supplied, server-
        # validated (tenant/patient/Admission-matching) existing record.
        sa.Column("requires_poc_change", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("linked_poc_problem_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("linked_poc_goal_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("linked_poc_intervention_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("reviewed_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["admission_id"], ["admissions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["idg_review_id"], ["idg_reviews.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["discipline_service_id"], ["patient_discipline_services.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["related_patient_issue_id"], ["patient_issues.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["linked_poc_problem_id"], ["poc_problems.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["linked_poc_goal_id"], ["poc_goals.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["linked_poc_intervention_id"], ["poc_interventions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["reviewed_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_idg_recommendations_tenant_id", "idg_recommendations", ["tenant_id"], unique=False)
    op.create_index("ix_idg_recommendations_patient_id", "idg_recommendations", ["patient_id"], unique=False)
    op.create_index("ix_idg_recommendations_admission_id", "idg_recommendations", ["admission_id"], unique=False)
    op.create_index("ix_idg_recommendations_idg_review_id", "idg_recommendations", ["idg_review_id"], unique=False)
    op.create_index("ix_idg_recommendations_discipline_service_id", "idg_recommendations", ["discipline_service_id"], unique=False)
    op.create_index("ix_idg_recommendations_status", "idg_recommendations", ["status"], unique=False)
    op.create_index("ix_idg_recommendations_tenant_patient", "idg_recommendations", ["tenant_id", "patient_id"], unique=False)
    op.create_index("ix_idg_recommendations_created_by", "idg_recommendations", ["created_by"], unique=False)
    op.create_index("ix_idg_recommendations_linked_poc_problem_id", "idg_recommendations", ["linked_poc_problem_id"], unique=False)
    op.create_index("ix_idg_recommendations_linked_poc_goal_id", "idg_recommendations", ["linked_poc_goal_id"], unique=False)
    op.create_index("ix_idg_recommendations_linked_poc_intervention_id", "idg_recommendations", ["linked_poc_intervention_id"], unique=False)

    # ---------------------------------------------------------------
    # patient_issues -- additive columns only. `status` is UNCHANGED.
    # ---------------------------------------------------------------
    op.add_column("patient_issues", sa.Column("issue_domain", sa.String(length=32), nullable=True))
    op.add_column("patient_issues", sa.Column("clinical_status", sa.String(length=20), nullable=True))
    op.add_column("patient_issues", sa.Column("severity_or_risk", sa.String(length=20), nullable=True))
    op.add_column("patient_issues", sa.Column("monitoring_owner_user_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("patient_issues", sa.Column("monitoring_owner_role", sa.String(length=32), nullable=True))
    op.add_column("patient_issues", sa.Column("related_discipline_service_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("patient_issues", sa.Column("related_refusal_event_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("patient_issues", sa.Column("latest_assessment_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("patient_issues", sa.Column("idg_review_required", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("patient_issues", sa.Column("next_review_at", sa.DateTime(timezone=True), nullable=True))

    op.create_foreign_key(
        "fk_patient_issues_monitoring_owner_user",
        "patient_issues",
        "users",
        ["monitoring_owner_user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_patient_issues_related_discipline_service",
        "patient_issues",
        "patient_discipline_services",
        ["related_discipline_service_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_patient_issues_related_refusal_event",
        "patient_issues",
        "patient_discipline_service_events",
        ["related_refusal_event_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_patient_issues_related_discipline_service_id", "patient_issues", ["related_discipline_service_id"], unique=False)
    op.create_index("ix_patient_issues_issue_domain", "patient_issues", ["issue_domain"], unique=False)
    op.create_index("ix_patient_issues_clinical_status", "patient_issues", ["clinical_status"], unique=False)


def downgrade() -> None:
    # Postgres cannot drop enum values added via ALTER TYPE ... ADD VALUE;
    # 'VOLUNTEER' / 'VOLUNTEER_REOFFER' remain defined but unused on
    # downgrade (same accepted limitation as b2c3d4e5f6a7).
    op.drop_index("ix_patient_issues_clinical_status", table_name="patient_issues")
    op.drop_index("ix_patient_issues_issue_domain", table_name="patient_issues")
    op.drop_index("ix_patient_issues_related_discipline_service_id", table_name="patient_issues")
    op.drop_constraint("fk_patient_issues_related_refusal_event", "patient_issues", type_="foreignkey")
    op.drop_constraint("fk_patient_issues_related_discipline_service", "patient_issues", type_="foreignkey")
    op.drop_constraint("fk_patient_issues_monitoring_owner_user", "patient_issues", type_="foreignkey")

    op.drop_column("patient_issues", "next_review_at")
    op.drop_column("patient_issues", "idg_review_required")
    op.drop_column("patient_issues", "latest_assessment_id")
    op.drop_column("patient_issues", "related_refusal_event_id")
    op.drop_column("patient_issues", "related_discipline_service_id")
    op.drop_column("patient_issues", "monitoring_owner_role")
    op.drop_column("patient_issues", "monitoring_owner_user_id")
    op.drop_column("patient_issues", "severity_or_risk")
    op.drop_column("patient_issues", "clinical_status")
    op.drop_column("patient_issues", "issue_domain")

    op.drop_table("idg_recommendations")

    op.drop_constraint("fk_pds_current_state_event", "patient_discipline_services", type_="foreignkey")
    op.drop_table("patient_discipline_service_events")
    op.drop_table("patient_discipline_services")
