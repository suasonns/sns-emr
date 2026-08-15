"""add patient_admissions table

Revision ID: 7d0f52b0485a
Revises: 6f22bbf50b8b
Create Date: 2026-07-15 22:40:21.166994
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "7d0f52b0485a"
down_revision: Union[str, Sequence[str], None] = "6f22bbf50b8b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "patient_admissions",

        # -----------------------------------
        # PRIMARY KEYS
        # -----------------------------------
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),

        # -----------------------------------
        # RELATIONSHIP ✅ CRITICAL
        # -----------------------------------
        sa.Column(
            "patient_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("patients.id", ondelete="CASCADE"),
            nullable=False,
        ),

        # -----------------------------------
        # STATUS
        # -----------------------------------
        sa.Column("status", sa.String(), nullable=False),

        # -----------------------------------
        # CORE DATES
        # -----------------------------------
        sa.Column("effective_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("soc_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("admitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("discharged_at", sa.DateTime(timezone=True), nullable=True),

        # -----------------------------------
        # COMPLIANCE TRACKING
        # -----------------------------------
        sa.Column("election_signed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("certification_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("physician_order_signed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("initial_assessment_completed_at", sa.DateTime(timezone=True), nullable=True),

        # -----------------------------------
        # AUDIT FIELDS ✅ REQUIRED
        # -----------------------------------
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=True,
        ),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
    )

    # -----------------------------------
    # INDEXES ✅ PERFORMANCE + TENANT SAFETY
    # -----------------------------------
    op.create_index(
        "ix_patient_admissions_patient_id",
        "patient_admissions",
        ["patient_id"],
    )

    op.create_index(
        "ix_patient_admissions_tenant_id",
        "patient_admissions",
        ["tenant_id"],
    )

    op.create_index(
        "ix_patient_admissions_status",
        "patient_admissions",
        ["status"],
    )

    # ✅ composite (common query path)
    op.create_index(
        "ix_patient_admissions_patient_tenant",
        "patient_admissions",
        ["tenant_id", "patient_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_patient_admissions_patient_tenant", table_name="patient_admissions")
    op.drop_index("ix_patient_admissions_status", table_name="patient_admissions")
    op.drop_index("ix_patient_admissions_tenant_id", table_name="patient_admissions")
    op.drop_index("ix_patient_admissions_patient_id", table_name="patient_admissions")

    op.drop_table("patient_admissions")