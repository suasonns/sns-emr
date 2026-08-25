"""add noe_edi_submissions table + patients NOTR tracking columns

Revision ID: 9a8c04c006b3
Revises: fe9eb2571468
Create Date: 2026-08-26

Real electronic NOE (TOB 81A) / NOTR (TOB 81B) 837I submission tracking
(noe_edi_submissions), plus the two real, biller-entered NOTR compliance
fields on patients (notr_submitted_date, notr_exception_reason) that
notr_penalty_service.compute_notr_penalty() needs -- mirrors the existing
benefit_periods.noe_submitted_date / noe_exception_reason pattern for the
NOE side.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "9a8c04c006b3"
down_revision = "fe9eb2571468"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("patients", sa.Column("notr_submitted_date", sa.Date(), nullable=True))
    op.add_column("patients", sa.Column("notr_exception_reason", sa.String(length=255), nullable=True))

    op.create_table(
        "noe_edi_submissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "patient_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("patients.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "benefit_period_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("benefit_periods.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("submission_type", sa.String(length=8), nullable=False),
        sa.Column("tob_code", sa.String(length=3), nullable=False),
        sa.Column("control_number", sa.String(length=64), nullable=False),
        sa.Column("effective_date", sa.Date(), nullable=False),
        sa.Column("edi_text", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="GENERATED"),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ack_status", sa.String(length=32), nullable=True),
        sa.Column("ack_raw_content", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_noe_edi_submissions_tenant_id", "noe_edi_submissions", ["tenant_id"]
    )
    op.create_index(
        "ix_noe_edi_submissions_patient_id", "noe_edi_submissions", ["patient_id"]
    )
    op.create_index(
        "ix_noe_edi_submissions_tenant_patient",
        "noe_edi_submissions",
        ["tenant_id", "patient_id"],
    )
    op.create_index(
        "ix_noe_edi_submissions_patient_type",
        "noe_edi_submissions",
        ["patient_id", "submission_type"],
    )
    op.create_index(
        "ix_noe_edi_submissions_status", "noe_edi_submissions", ["status"]
    )


def downgrade() -> None:
    op.drop_index("ix_noe_edi_submissions_status", table_name="noe_edi_submissions")
    op.drop_index("ix_noe_edi_submissions_patient_type", table_name="noe_edi_submissions")
    op.drop_index("ix_noe_edi_submissions_tenant_patient", table_name="noe_edi_submissions")
    op.drop_index("ix_noe_edi_submissions_patient_id", table_name="noe_edi_submissions")
    op.drop_index("ix_noe_edi_submissions_tenant_id", table_name="noe_edi_submissions")
    op.drop_table("noe_edi_submissions")

    op.drop_column("patients", "notr_exception_reason")
    op.drop_column("patients", "notr_submitted_date")
