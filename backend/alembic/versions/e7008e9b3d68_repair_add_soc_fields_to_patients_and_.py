"""
repair_add_soc_fields_to_patients_and_due_at_to_tasks

Revision ID: e7008e9b3d68
Revises: df42011a7ffc
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "e7008e9b3d68"
down_revision = "df42011a7ffc"
branch_labels = None
depends_on = None


def _column_exists(bind, table: str, column: str, schema: str = "public") -> bool:
    sql = sa.text(
        """
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = :schema
          AND table_name = :table
          AND column_name = :column
        """
    )
    return bind.execute(sql, {"schema": schema, "table": table, "column": column}).first() is not None


def _constraint_exists(bind, table: str, constraint: str, schema: str = "public") -> bool:
    sql = sa.text(
        """
        SELECT 1
        FROM pg_constraint c
        JOIN pg_class t ON t.oid = c.conrelid
        JOIN pg_namespace n ON n.oid = t.relnamespace
        WHERE n.nspname = :schema
          AND t.relname = :table
          AND c.conname = :constraint
        """
    )
    return bind.execute(sql, {"schema": schema, "table": table, "constraint": constraint}).first() is not None


def upgrade() -> None:
    bind = op.get_bind()

    # ---------------------------------------------------------
    # patients SOC / admission fields (idempotent)
    # ---------------------------------------------------------
    if not _column_exists(bind, "patients", "records_release_signed_at"):
        op.add_column(
            "patients",
            sa.Column("records_release_signed_at", sa.DateTime(timezone=True), nullable=True),
        )

    if not _column_exists(bind, "patients", "election_signed_at"):
        op.add_column(
            "patients",
            sa.Column("election_signed_at", sa.DateTime(timezone=True), nullable=True),
        )

    if not _column_exists(bind, "patients", "soc_date"):
        op.add_column(
            "patients",
            sa.Column("soc_date", sa.DateTime(timezone=True), nullable=True),
        )

    if not _column_exists(bind, "patients", "admission_status"):
        # server_default only to satisfy NOT NULL on existing rows
        op.add_column(
            "patients",
            sa.Column(
                "admission_status",
                sa.String(length=32),
                nullable=False,
                server_default="PRE_REFERRAL",
            ),
        )
        # remove default after backfill (enterprise cleanliness)
        op.alter_column("patients", "admission_status", server_default=None)

    if not _column_exists(bind, "patients", "admission_authorized_at"):
        op.add_column(
            "patients",
            sa.Column("admission_authorized_at", sa.DateTime(timezone=True), nullable=True),
        )

    if not _column_exists(bind, "patients", "admission_authorized_by"):
        op.add_column(
            "patients",
            sa.Column("admission_authorized_by", postgresql.UUID(as_uuid=True), nullable=True),
        )

    if not _column_exists(bind, "patients", "not_admitted_at"):
        op.add_column(
            "patients",
            sa.Column("not_admitted_at", sa.DateTime(timezone=True), nullable=True),
        )

    if not _column_exists(bind, "patients", "not_admitted_reason"):
        op.add_column(
            "patients",
            sa.Column("not_admitted_reason", sa.Text(), nullable=True),
        )

    if not _constraint_exists(bind, "patients", "ck_patients_admission_status"):
        op.create_check_constraint(
            "ck_patients_admission_status",
            "patients",
            "admission_status IN ("
            "'PRE_REFERRAL',"
            "'RECORDS_PENDING',"
            "'MD_REVIEW_PENDING',"
            "'AUTHORIZED_TO_ADMIT',"
            "'ADMITTED',"
            "'NOT_ADMITTED'"
            ")",
        )

    # ---------------------------------------------------------
    # tasks due_at (idempotent)
    # ---------------------------------------------------------
    if not _column_exists(bind, "tasks", "due_at"):
        op.add_column(
            "tasks",
            sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        )


def downgrade() -> None:
    # Forward-only repair migration for compliance/audit safety.
    pass
