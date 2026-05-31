"""
apply_soc_admission_fields_and_task_due_at

Revision ID: df42011a7ffc
Revises: 4884993d938a
Create Date: 2026-05-29 16:01:32
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# -------------------------------------------------
# Alembic identifiers
# -------------------------------------------------

revision: str = "df42011a7ffc"
down_revision: Union[str, Sequence[str], None] = "4884993d938a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# -------------------------------------------------
# Upgrade
# -------------------------------------------------

def upgrade() -> None:
    # -------------------------
    # patients table
    # -------------------------
    op.add_column(
        "patients",
        sa.Column("records_release_signed_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.add_column(
        "patients",
        sa.Column("election_signed_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.add_column(
        "patients",
        sa.Column("soc_date", sa.DateTime(timezone=True), nullable=True),
    )

    # admission_status requires NOT NULL; use temporary default for backfill
    op.add_column(
        "patients",
        sa.Column(
            "admission_status",
            sa.String(length=32),
            nullable=False,
            server_default="PRE_REFERRAL",
        ),
    )

    # remove default after existing rows are satisfied
    op.alter_column("patients", "admission_status", server_default=None)

    op.add_column(
        "patients",
        sa.Column("admission_authorized_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.add_column(
        "patients",
        sa.Column(
            "admission_authorized_by",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )

    op.add_column(
        "patients",
        sa.Column("not_admitted_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.add_column(
        "patients",
        sa.Column("not_admitted_reason", sa.Text(), nullable=True),
    )

    # admission_status constraint (PostgreSQL-safe)
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
    op.add_column(
        "tasks",
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
    )


# -------------------------------------------------
# Downgrade
# -------------------------------------------------

def downgrade() -> None:
    # Forward-only migration for compliance and audit safety.
    pass