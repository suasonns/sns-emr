"""add payer eligibility checks + patient_insurance tracking fields

Revision ID: a2d6f8b1c4e9
Revises: f3a9c1e7b5d0
Create Date: 2026-08-24

Real, persisted payer eligibility verification history
(payer_eligibility_checks), plus eligibility_status /
next_verification_due tracking columns on patient_insurances. This is
NOT tied to a live 270/271 clearinghouse feed -- that integration
doesn't exist yet in this system -- but gives billers a real place to
log verification results (manual today, automated batch later) instead
of a fabricated/in-memory eligibility status.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "a2d6f8b1c4e9"
down_revision = "f3a9c1e7b5d0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "patient_insurances",
        sa.Column(
            "eligibility_status",
            sa.String(length=32),
            nullable=True,
            server_default="UNKNOWN",
        ),
    )
    op.add_column(
        "patient_insurances",
        sa.Column("next_verification_due", sa.Date(), nullable=True),
    )
    op.create_index(
        "ix_patient_insurances_eligibility_status",
        "patient_insurances",
        ["eligibility_status"],
    )

    op.create_table(
        "payer_eligibility_checks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "patient_insurance_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("patient_insurances.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "checked_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("check_method", sa.String(length=32), nullable=False, server_default="MANUAL"),
        sa.Column("result_status", sa.String(length=32), nullable=False, server_default="UNKNOWN"),
        sa.Column("payer_response_code", sa.String(length=32), nullable=True),
        sa.Column("plan_begin_date", sa.Date(), nullable=True),
        sa.Column("plan_end_date", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("checked_by", sa.String(length=255), nullable=True),
        sa.Column("raw_response", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_payer_eligibility_checks_tenant_id", "payer_eligibility_checks", ["tenant_id"]
    )
    op.create_index(
        "ix_payer_eligibility_checks_patient_insurance_id",
        "payer_eligibility_checks",
        ["patient_insurance_id"],
    )
    op.create_index(
        "ix_payer_eligibility_checks_result_status",
        "payer_eligibility_checks",
        ["result_status"],
    )
    op.create_index(
        "ix_payer_eligibility_check_insurance_checked_at",
        "payer_eligibility_checks",
        ["patient_insurance_id", "checked_at"],
    )
    op.create_index(
        "ix_payer_eligibility_check_tenant_status",
        "payer_eligibility_checks",
        ["tenant_id", "result_status"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_payer_eligibility_check_tenant_status", table_name="payer_eligibility_checks"
    )
    op.drop_index(
        "ix_payer_eligibility_check_insurance_checked_at",
        table_name="payer_eligibility_checks",
    )
    op.drop_index(
        "ix_payer_eligibility_checks_result_status", table_name="payer_eligibility_checks"
    )
    op.drop_index(
        "ix_payer_eligibility_checks_patient_insurance_id",
        table_name="payer_eligibility_checks",
    )
    op.drop_index(
        "ix_payer_eligibility_checks_tenant_id", table_name="payer_eligibility_checks"
    )
    op.drop_table("payer_eligibility_checks")

    op.drop_index(
        "ix_patient_insurances_eligibility_status", table_name="patient_insurances"
    )
    op.drop_column("patient_insurances", "next_verification_due")
    op.drop_column("patient_insurances", "eligibility_status")
