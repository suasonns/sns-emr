"""add bereavement cases tasks declines and volunteer hours

Revision ID: 2ad2748d79bf
Revises: 5c245a593175
Create Date: 2026-05-05 10:32:33.674391

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '2ad2748d79bf'
down_revision: Union[str, Sequence[str], None] = '5c245a593175'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


"""add bereavement cases tasks declines and volunteer hours

Revises: 5c245a593175
Create Date: 2026-05-05
"""


def upgrade():
    # ------------------------------------------------------------
    # 1) Create PostgreSQL enum types safely (idempotent)
    # ------------------------------------------------------------
    op.execute("""
    DO $$
    BEGIN
        CREATE TYPE bereavement_case_status AS ENUM ('ACTIVE','CLOSED');
    EXCEPTION
        WHEN duplicate_object THEN NULL;
    END $$;
    """)

    op.execute("""
    DO $$
    BEGIN
        CREATE TYPE bereavement_task_subtype AS ENUM (
            'SYMPATHY_CARD',
            'CARD_30_DAY',
            'CARD_60_DAY',
            'CARD_90_DAY',
            'ANNIVERSARY_CARD',
            'BEREAVEMENT_CALL',
            'BEREAVEMENT_COUNSELING'
        );
    EXCEPTION
        WHEN duplicate_object THEN NULL;
    END $$;
    """)

    op.execute("""
    DO $$
    BEGIN
        CREATE TYPE bereavement_task_status AS ENUM ('PENDING','COMPLETED','OVERDUE');
    EXCEPTION
        WHEN duplicate_object THEN NULL;
    END $$;
    """)

    op.execute("""
    DO $$
    BEGIN
        CREATE TYPE bereavement_role AS ENUM ('MSW','SC','RN');
    EXCEPTION
        WHEN duplicate_object THEN NULL;
    END $$;
    """)

    op.execute("""
    DO $$
    BEGIN
        CREATE TYPE bereavement_decline_reason AS ENUM (
            'FAMILY_DECLINED_SERVICE',
            'SERVICE_NOT_DESIRED',
            'STAFF_UNAVAILABLE',
            'CULTURAL_PREFERENCE'
        );
    EXCEPTION
        WHEN duplicate_object THEN NULL;
    END $$;
    """)

    op.execute("""
    DO $$
    BEGIN
        CREATE TYPE volunteer_activity_type AS ENUM ('ADMIN','DIRECT_PATIENT_SUPPORT');
    EXCEPTION
        WHEN duplicate_object THEN NULL;
    END $$;
    """)

    # ------------------------------------------------------------
    # 2) bereavement_cases
    # ------------------------------------------------------------
    op.create_table(
        "bereavement_cases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),

        # 13-month bereavement window is enforced in application logic;
        # DB stores start/end for auditing and reporting.
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),

        sa.Column("status", postgresql.ENUM(name="bereavement_case_status", create_type=False),
                  nullable=False, server_default="ACTIVE"),

        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_index("ix_bereavement_cases_patient_id", "bereavement_cases", ["patient_id"])
    op.create_index("ix_bereavement_cases_status", "bereavement_cases", ["status"])
    op.create_index("ix_bereavement_cases_end_date", "bereavement_cases", ["end_date"])

    # ------------------------------------------------------------
    # 3) bereavement_tasks
    # ------------------------------------------------------------
    op.create_table(
        "bereavement_tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("bereavement_case_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("bereavement_cases.id", ondelete="CASCADE"), nullable=False),

        sa.Column("task_subtype", postgresql.ENUM(name="bereavement_task_subtype", create_type=False),
                  nullable=False),

        sa.Column("due_date", sa.Date(), nullable=False),

        sa.Column("status", postgresql.ENUM(name="bereavement_task_status", create_type=False),
                  nullable=False, server_default="PENDING"),

        # Primary roles allowed: MSW/SC; RN only allowed after decline is documented.
        # Stored for auditability and UI rendering; enforcement via constraints below.
        sa.Column("primary_roles_allowed", postgresql.ARRAY(sa.String(length=8)), nullable=False,
                  server_default=sa.text("ARRAY['MSW','SC']::text[]")),
        sa.Column("fallback_role", postgresql.ENUM(name="bereavement_role", create_type=False),
                  nullable=False, server_default="RN"),
        sa.Column("decline_record_exists", sa.Boolean(), nullable=False, server_default=sa.text("false")),

        # Completion metadata
        sa.Column("completed_by_user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("completed_by_role", postgresql.ENUM(name="bereavement_role", create_type=False),
                  nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),

        # Evidence and exceptions (no FK to documents to avoid coupling if docs table not final yet)
        sa.Column("evidence_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("exception_reason", sa.Text(), nullable=True),

        # Compliance: bereavement is never billable
        sa.Column("billable", sa.Boolean(), nullable=False, server_default=sa.text("false")),

        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_index("ix_bereavement_tasks_case_id", "bereavement_tasks", ["bereavement_case_id"])
    op.create_index("ix_bereavement_tasks_due_date", "bereavement_tasks", ["due_date"])
    op.create_index("ix_bereavement_tasks_status", "bereavement_tasks", ["status"])
    op.create_index("ix_bereavement_tasks_subtype", "bereavement_tasks", ["task_subtype"])

    # --- Hard constraints (survey-defensible) ---
    # 1) billable must always be false
    op.create_check_constraint(
        "ck_bereavement_tasks_not_billable",
        "bereavement_tasks",
        "billable = false"
    )

    # 2) COMPLETED requires completed_at and completed_by_user_id
    op.create_check_constraint(
        "ck_bereavement_tasks_completed_requires_metadata",
        "bereavement_tasks",
        "(status <> 'COMPLETED') OR (completed_at IS NOT NULL AND completed_by_user_id IS NOT NULL AND completed_by_role IS NOT NULL)"
    )

    # 3) COMPLETED requires evidence or exception_reason
    op.create_check_constraint(
        "ck_bereavement_tasks_completed_requires_evidence_or_exception",
        "bereavement_tasks",
        "(status <> 'COMPLETED') OR (evidence_id IS NOT NULL OR exception_reason IS NOT NULL)"
    )

    # 4) RN completion requires documented decline
    op.create_check_constraint(
        "ck_bereavement_tasks_rn_requires_decline",
        "bereavement_tasks",
        "(completed_by_role IS NULL) OR (completed_by_role <> 'RN') OR (decline_record_exists = true)"
    )

    # ------------------------------------------------------------
    # 4) bereavement_declines
    # ------------------------------------------------------------
    op.create_table(
        "bereavement_declines",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("bereavement_task_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("bereavement_tasks.id", ondelete="CASCADE"), nullable=False),

        sa.Column("declined_role", postgresql.ENUM(name="bereavement_role", create_type=False), nullable=False),
        sa.Column("decline_reason", postgresql.ENUM(name="bereavement_decline_reason", create_type=False), nullable=False),

        sa.Column("recorded_by_user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_index("ix_bereavement_declines_task_id", "bereavement_declines", ["bereavement_task_id"])
    op.create_index("ix_bereavement_declines_role", "bereavement_declines", ["declined_role"])

    # ------------------------------------------------------------
    # 5) volunteer_hours (CMS 418.78 tracking)
    # ------------------------------------------------------------
    op.create_table(
        "volunteer_hours",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),

        # volunteer may be modeled as a user account with role=VOLUNTEER
        sa.Column("volunteer_user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),

        sa.Column("date", sa.Date(), nullable=False),

        # store decimal hours (e.g., 1.50); enforce > 0
        sa.Column("hours", sa.Numeric(5, 2), nullable=False),

        sa.Column("activity_type", postgresql.ENUM(name="volunteer_activity_type", create_type=False), nullable=False),

        # supervision is required by a designated hospice employee
        sa.Column("supervised_by_user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),

        sa.Column("counts_for_5_percent", sa.Boolean(), nullable=False, server_default=sa.text("true")),

        sa.Column("notes", sa.Text(), nullable=True),

        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_index("ix_volunteer_hours_volunteer_user_id", "volunteer_hours", ["volunteer_user_id"])
    op.create_index("ix_volunteer_hours_date", "volunteer_hours", ["date"])
    op.create_index("ix_volunteer_hours_activity_type", "volunteer_hours", ["activity_type"])

    op.create_check_constraint(
        "ck_volunteer_hours_positive",
        "volunteer_hours",
        "hours > 0"
    )


def downgrade():
    # Drop tables in reverse dependency order
    op.drop_constraint("ck_volunteer_hours_positive", "volunteer_hours", type_="check")
    op.drop_index("ix_volunteer_hours_activity_type", table_name="volunteer_hours")
    op.drop_index("ix_volunteer_hours_date", table_name="volunteer_hours")
    op.drop_index("ix_volunteer_hours_volunteer_user_id", table_name="volunteer_hours")
    op.drop_table("volunteer_hours")

    op.drop_index("ix_bereavement_declines_role", table_name="bereavement_declines")
    op.drop_index("ix_bereavement_declines_task_id", table_name="bereavement_declines")
    op.drop_table("bereavement_declines")

    op.drop_constraint("ck_bereavement_tasks_rn_requires_decline", "bereavement_tasks", type_="check")
    op.drop_constraint("ck_bereavement_tasks_completed_requires_evidence_or_exception", "bereavement_tasks", type_="check")
    op.drop_constraint("ck_bereavement_tasks_completed_requires_metadata", "bereavement_tasks", type_="check")
    op.drop_constraint("ck_bereavement_tasks_not_billable", "bereavement_tasks", type_="check")

    op.drop_index("ix_bereavement_tasks_subtype", table_name="bereavement_tasks")
    op.drop_index("ix_bereavement_tasks_status", table_name="bereavement_tasks")
    op.drop_index("ix_bereavement_tasks_due_date", table_name="bereavement_tasks")
    op.drop_index("ix_bereavement_tasks_case_id", table_name="bereavement_tasks")
    op.drop_table("bereavement_tasks")

    op.drop_index("ix_bereavement_cases_end_date", table_name="bereavement_cases")
    op.drop_index("ix_bereavement_cases_status", table_name="bereavement_cases")
    op.drop_index("ix_bereavement_cases_patient_id", table_name="bereavement_cases")
    op.drop_table("bereavement_cases")

    # Drop enum types last (may fail if something else still depends on them)
    op.execute("DROP TYPE IF EXISTS volunteer_activity_type;")
    op.execute("DROP TYPE IF EXISTS bereavement_decline_reason;")
    op.execute("DROP TYPE IF EXISTS bereavement_role;")
    op.execute("DROP TYPE IF EXISTS bereavement_task_status;")
    op.execute("DROP TYPE IF EXISTS bereavement_task_subtype;")
    op.execute("DROP TYPE IF EXISTS bereavement_case_status;")
