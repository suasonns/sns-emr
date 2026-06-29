"""add clinical plan of care engine

Revision ID: 428042f48054
Revises: 1e3197fad3dd
Create Date: 2026-06-26 17:06:50.121232

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '428042f48054'
down_revision: Union[str, Sequence[str], None] = '1e3197fad3dd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


UUID = postgresql.UUID(as_uuid=True)
JSONB = postgresql.JSONB(astext_type=sa.Text())


def upgrade():
    # ---------------------------------------------------------
    # plan_of_care
    # ---------------------------------------------------------
    op.create_table(
        "plan_of_care",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),

        sa.Column("patient_id", UUID, nullable=False),
        sa.Column("tenant_id", UUID, nullable=False),

        sa.Column("status", sa.String(length=32), nullable=False, server_default="DRAFT"),
        sa.Column("version_number", sa.Integer(), nullable=False, server_default="1"),

        sa.Column("effective_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_reviewed_at", sa.DateTime(timezone=True), nullable=True),

        sa.Column("rn_coordinator_user_id", UUID, nullable=True),
        sa.Column("attending_physician_name", sa.String(length=255), nullable=True),
        sa.Column("medical_director_user_id", UUID, nullable=True),

        sa.Column("approval_status", sa.String(length=32), nullable=False, server_default="PENDING"),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_by_user_id", UUID, nullable=True),

        sa.Column("supersedes_plan_of_care_id", UUID, nullable=True),
        sa.Column("current_version_id", UUID, nullable=True),

        # PRODUCTION MINIMUM: real clinical POC content lives here
        sa.Column(
            "poc_content_json",
            JSONB,
            nullable=False,
            server_default=sa.text("'{}'::jsonb")
        ),

        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),

        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["patients.id"],
            name="fk_plan_of_care_patient_id_patients",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["supersedes_plan_of_care_id"],
            ["plan_of_care.id"],
            name="fk_plan_of_care_supersedes_self",
        ),

        sa.CheckConstraint(
            "status IN ('DRAFT','ACTIVE','SUPERSEDED','ARCHIVED')",
            name="ck_plan_of_care_status",
        ),
        sa.CheckConstraint(
            "approval_status IN ('PENDING','APPROVED','REJECTED')",
            name="ck_plan_of_care_approval_status",
        ),
        sa.CheckConstraint(
            "(approved_at IS NULL AND approved_by_user_id IS NULL) OR "
            "(approved_at IS NOT NULL AND approved_by_user_id IS NOT NULL)",
            name="ck_plan_of_care_approval_pair",
        ),
    )

    op.create_index("ix_plan_of_care_patient_id", "plan_of_care", ["patient_id"])
    op.create_index("ix_plan_of_care_tenant_id", "plan_of_care", ["tenant_id"])
    op.create_index("ix_plan_of_care_status", "plan_of_care", ["status"])
    op.create_index("ix_plan_of_care_review_due_at", "plan_of_care", ["review_due_at"])

    # ---------------------------------------------------------
    # plan_of_care_versions
    # ---------------------------------------------------------
    op.create_table(
        "plan_of_care_versions",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("plan_of_care_id", UUID, nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),

        sa.Column(
            "snapshot_json",
            JSONB,
            nullable=False,
            server_default=sa.text("'{}'::jsonb")
        ),

        sa.Column("change_reason", sa.Text(), nullable=True),
        sa.Column("trigger_source", sa.String(length=64), nullable=True),

        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by", UUID, nullable=True),

        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_by_user_id", UUID, nullable=True),

        sa.ForeignKeyConstraint(
            ["plan_of_care_id"],
            ["plan_of_care.id"],
            name="fk_plan_of_care_versions_plan_of_care_id",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "plan_of_care_id",
            "version_number",
            name="uq_plan_of_care_versions_plan_version",
        ),
    )

    op.create_index(
        "ix_plan_of_care_versions_plan_of_care_id",
        "plan_of_care_versions",
        ["plan_of_care_id"],
    )

    # now that versions exists, add current_version_id FK
    op.create_foreign_key(
        "fk_plan_of_care_current_version_id_versions",
        "plan_of_care",
        "plan_of_care_versions",
        ["current_version_id"],
        ["id"],
    )

    # ---------------------------------------------------------
    # plan_of_care_goals
    # ---------------------------------------------------------
    op.create_table(
        "plan_of_care_goals",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("plan_of_care_id", UUID, nullable=False),

        sa.Column("problem_code", sa.String(length=128), nullable=True),
        sa.Column("problem_label", sa.String(length=255), nullable=False),

        sa.Column("goal_text", sa.Text(), nullable=False),
        sa.Column("outcome_measure", sa.Text(), nullable=True),
        sa.Column("target_date", sa.Date(), nullable=True),

        sa.Column("status", sa.String(length=32), nullable=False, server_default="ACTIVE"),
        sa.Column("discipline_owner", sa.String(length=64), nullable=True),
        sa.Column("progress_summary", sa.Text(), nullable=True),

        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),

        sa.ForeignKeyConstraint(
            ["plan_of_care_id"],
            ["plan_of_care.id"],
            name="fk_plan_of_care_goals_plan_of_care_id",
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "status IN ('ACTIVE','MET','NOT_MET','DISCONTINUED')",
            name="ck_plan_of_care_goals_status",
        ),
    )

    op.create_index(
        "ix_plan_of_care_goals_plan_of_care_id",
        "plan_of_care_goals",
        ["plan_of_care_id"],
    )

    # ---------------------------------------------------------
    # plan_of_care_approvals
    # ---------------------------------------------------------
    op.create_table(
        "plan_of_care_approvals",
        sa.Column("id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("plan_of_care_id", UUID, nullable=False),
        sa.Column("version_id", UUID, nullable=False),

        sa.Column("approver_role", sa.String(length=64), nullable=False),
        sa.Column("approver_user_id", UUID, nullable=True),

        sa.Column("decision", sa.String(length=32), nullable=False, server_default="PENDING"),
        sa.Column("decision_note", sa.Text(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),

        sa.ForeignKeyConstraint(
            ["plan_of_care_id"],
            ["plan_of_care.id"],
            name="fk_plan_of_care_approvals_plan_of_care_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["version_id"],
            ["plan_of_care_versions.id"],
            name="fk_plan_of_care_approvals_version_id",
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "decision IN ('PENDING','APPROVED','REJECTED')",
            name="ck_plan_of_care_approvals_decision",
        ),
    )

    op.create_index(
        "ix_plan_of_care_approvals_plan_of_care_id",
        "plan_of_care_approvals",
        ["plan_of_care_id"],
    )
    op.create_index(
        "ix_plan_of_care_approvals_version_id",
        "plan_of_care_approvals",
        ["version_id"],
    )


def downgrade():
    op.drop_table("plan_of_care_approvals")
    op.drop_table("plan_of_care_goals")
    op.drop_table("plan_of_care_versions")
    op.drop_table("plan_of_care")