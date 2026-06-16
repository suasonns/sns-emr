"""
repair_add_soc_fields_to_patients_and_due_at_to_tasks (ENTERPRISE REBUILD-SAFE)

Revision ID: e7008e9b3d68
Revises: df42011a7ffc
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

revision = "e7008e9b3d68"
down_revision = "df42011a7ffc"
branch_labels = None
depends_on = None


# -----------------------------------------------------
# Helpers (IDEMPOTENT)
# -----------------------------------------------------

def _column_exists(inspector, table: str, column: str) -> bool:
    return column in {col["name"] for col in inspector.get_columns(table)}


def _constraint_exists(bind, table: str, candidates: list[str]) -> bool:
    sql = sa.text(
        """
        SELECT c.conname
        FROM pg_constraint c
        JOIN pg_class t ON t.oid = c.conrelid
        JOIN pg_namespace n ON n.oid = t.relnamespace
        WHERE t.relname = :table AND n.nspname = 'public'
        """
    )

    existing = {
        row[0]
        for row in bind.execute(sql, {"table": table})
    }

    return any(name in existing for name in candidates)


# -----------------------------------------------------
# Upgrade
# -----------------------------------------------------

def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    # -------------------------------------------------
    # patients SOC / admission fields
    # -------------------------------------------------

    if "patients" in inspector.get_table_names():

        if not _column_exists(inspector, "patients", "records_release_signed_at"):
            op.add_column(
                "patients",
                sa.Column("records_release_signed_at", sa.DateTime(timezone=True), nullable=True),
            )

        if not _column_exists(inspector, "patients", "election_signed_at"):
            op.add_column(
                "patients",
                sa.Column("election_signed_at", sa.DateTime(timezone=True), nullable=True),
            )

        if not _column_exists(inspector, "patients", "soc_date"):
            op.add_column(
                "patients",
                sa.Column("soc_date", sa.DateTime(timezone=True), nullable=True),
            )

        if not _column_exists(inspector, "patients", "admission_status"):
            op.add_column(
                "patients",
                sa.Column(
                    "admission_status",
                    sa.String(length=32),
                    nullable=False,
                    server_default="PRE_REFERRAL",
                ),
            )
            op.alter_column("patients", "admission_status", server_default=None)

        if not _column_exists(inspector, "patients", "admission_authorized_at"):
            op.add_column(
                "patients",
                sa.Column("admission_authorized_at", sa.DateTime(timezone=True), nullable=True),
            )

        if not _column_exists(inspector, "patients", "admission_authorized_by"):
            op.add_column(
                "patients",
                sa.Column("admission_authorized_by", postgresql.UUID(as_uuid=True), nullable=True),
            )

        if not _column_exists(inspector, "patients", "not_admitted_at"):
            op.add_column(
                "patients",
                sa.Column("not_admitted_at", sa.DateTime(timezone=True), nullable=True),
            )

        if not _column_exists(inspector, "patients", "not_admitted_reason"):
            op.add_column(
                "patients",
                sa.Column("not_admitted_reason", sa.Text(), nullable=True),
            )

        # ✅ SAFE CONSTRAINT (handles legacy + duplicate naming)
        constraint_candidates = [
            "ck_patients_admission_status",
            "ck_patients_ck_patients_admission_status",
        ]

        if not _constraint_exists(bind, "patients", constraint_candidates):
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

    # -------------------------------------------------
    # tasks due_at
    # -------------------------------------------------

    if "tasks" in inspector.get_table_names():
        if not _column_exists(inspector, "tasks", "due_at"):
            op.add_column(
                "tasks",
                sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
            )


# -----------------------------------------------------
# Downgrade
# -----------------------------------------------------

def downgrade() -> None:
    # ✅ forward-only (audit safe)
    pass