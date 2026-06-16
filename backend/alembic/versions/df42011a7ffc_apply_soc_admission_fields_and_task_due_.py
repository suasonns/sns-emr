"""
apply_soc_admission_fields_and_task_due_at (REBUILD-SAFE)

Revision ID: df42011a7ffc
Revises: 4884993d938a
Create Date: 2026-05-29 16:01:32
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql


# -------------------------------------------------
# Alembic identifiers
# -------------------------------------------------

revision: str = "df42011a7ffc"
down_revision: Union[str, Sequence[str], None] = "4884993d938a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# -------------------------------------------------
# Helpers (idempotent / rebuild-safe)
# -------------------------------------------------

def _column_exists(inspector, table_name: str, column_name: str) -> bool:
    return column_name in {col["name"] for col in inspector.get_columns(table_name)}


def _constraint_exists(
    bind,
    table_name: str,
    constraint_names: list[str],
    schema: str = "public",
) -> bool:
    sql = sa.text(
        """
        SELECT c.conname
        FROM pg_constraint c
        JOIN pg_class t ON t.oid = c.conrelid
        JOIN pg_namespace n ON n.oid = t.relnamespace
        WHERE n.nspname = :schema
          AND t.relname = :table_name
        """
    )
    existing = {
        row[0]
        for row in bind.execute(
            sql,
            {"schema": schema, "table_name": table_name},
        )
    }
    return any(name in existing for name in constraint_names)


# -------------------------------------------------
# Upgrade
# -------------------------------------------------

def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    # -------------------------
    # patients table
    # -------------------------
    if "patients" in inspector.get_table_names():

        if not _column_exists(inspector, "patients", "records_release_signed_at"):
            op.add_column(
                "patients",
                sa.Column(
                    "records_release_signed_at",
                    sa.DateTime(timezone=True),
                    nullable=True,
                ),
            )

        if not _column_exists(inspector, "patients", "election_signed_at"):
            op.add_column(
                "patients",
                sa.Column(
                    "election_signed_at",
                    sa.DateTime(timezone=True),
                    nullable=True,
                ),
            )

        if not _column_exists(inspector, "patients", "soc_date"):
            op.add_column(
                "patients",
                sa.Column(
                    "soc_date",
                    sa.DateTime(timezone=True),
                    nullable=True,
                ),
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
                sa.Column(
                    "admission_authorized_at",
                    sa.DateTime(timezone=True),
                    nullable=True,
                ),
            )

        if not _column_exists(inspector, "patients", "admission_authorized_by"):
            op.add_column(
                "patients",
                sa.Column(
                    "admission_authorized_by",
                    postgresql.UUID(as_uuid=True),
                    nullable=True,
                ),
            )

        if not _column_exists(inspector, "patients", "not_admitted_at"):
            op.add_column(
                "patients",
                sa.Column(
                    "not_admitted_at",
                    sa.DateTime(timezone=True),
                    nullable=True,
                ),
            )

        if not _column_exists(inspector, "patients", "not_admitted_reason"):
            op.add_column(
                "patients",
                sa.Column(
                    "not_admitted_reason",
                    sa.Text(),
                    nullable=True,
                ),
            )

        # Refresh inspector after any possible column adds
        inspector = inspect(bind)

        # Support both legacy and normalized constraint names
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

    # -------------------------
    # tasks table
    # -------------------------
    inspector = inspect(bind)

    if "tasks" in inspector.get_table_names():
        if not _column_exists(inspector, "tasks", "due_at"):
            op.add_column(
                "tasks",
                sa.Column(
                    "due_at",
                    sa.DateTime(timezone=True),
                    nullable=True,
                ),
            )


# -------------------------------------------------
# Downgrade
# -------------------------------------------------

def downgrade() -> None:
    # Forward-only migration for compliance and audit safety.
    pass