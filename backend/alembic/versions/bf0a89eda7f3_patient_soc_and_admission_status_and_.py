"""
patient_soc_and_admission_status_and_task_due_at

Revision ID: bf0a89eda7f3
Revises: 122debb94552
Create Date: 2026-05-29 15:34:52
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# ---------------------------------------------------------
# Alembic identifiers
# ---------------------------------------------------------

revision: str = "bf0a89eda7f3"
down_revision: Union[str, Sequence[str], None] = "122debb94552"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ---------------------------------------------------------
# Constants
# ---------------------------------------------------------

ADMISSION_STATUSES = (
    "PRE_REFERRAL",
    "RECORDS_PENDING",
    "MD_REVIEW_PENDING",
    "AUTHORIZED_TO_ADMIT",
    "ADMITTED",
    "NOT_ADMITTED",
)


# ---------------------------------------------------------
# Upgrade
# ---------------------------------------------------------

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

    op.add_column(
        "patients",
        sa.Column(
            "admission_status",
            sa.String(length=32),
            nullable=False,
            server_default="PRE_REFERRAL",
        ),
    )

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

    # CHECK constraint (Postgres‑safe)
    op.create_check_constraint(
        "ck_patients_admission_status",
        "patients",
        "admission_status IN ('PRE_REFERRAL','RECORDS_PENDING','MD_REVIEW_PENDING','AUTHORIZED_TO_ADMIT','ADMITTED','NOT_ADMITTED')",
    )

    # Remove server default (enforce via app logic)
    op.alter_column(
        "patients",
        "admission_status",
        server_default=None,
    )

    # -------------------------
    # tasks table
    # -------------------------
    op.add_column(
        "tasks",
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
    )


# ---------------------------------------------------------
# Downgrade
# ---------------------------------------------------------

def downgrade() -> None:
    op.drop_column("tasks", "due_at")

    op.drop_constraint(
        "ck_patients_admission_status",
        "patients",
        type_="check",
    )

    op.drop_column("patients", "not_admitted_reason")
    op.drop_column("patients", "not_admitted_at")
    op.drop_column("patients", "admission_authorized_by")
    op.drop_column("patients", "admission_authorized_at")
    op.drop_column("patients", "admission_status")
    op.drop_column("patients", "soc_date")
    op.drop_column("patients", "election_signed_at")
    op.drop_column("patients", "records_release_signed_at")