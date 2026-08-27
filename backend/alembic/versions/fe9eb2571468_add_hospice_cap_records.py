"""add hospice_cap_records table

Revision ID: fe9eb2571468
Revises: a2d6f8b1c4e9
Create Date: 2026-08-26

Real, biller-entered per-cap-year inputs (beneficiary_count,
gross_reimbursement_collected) for the agency-level hospice aggregate cap
(42 CFR 418.309). hospice_cap_service.compute_agency_cap_usage() already
computes the correct cap dollar amount and usage percentage once given
these two numbers, but this system has no way to derive them itself --
they are cross-provider proportional figures that only exist on the
agency's real NGS PS&R cap report. This table gives billers/admins a
real place to log those figures instead of the app fabricating or
guessing agency-level cap usage.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "fe9eb2571468"
down_revision = "a2d6f8b1c4e9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "hospice_cap_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("cap_year", sa.Integer(), nullable=False),
        sa.Column("beneficiary_count", sa.Numeric(10, 4), nullable=False),
        sa.Column("gross_reimbursement_collected", sa.Numeric(14, 2), nullable=False),
        sa.Column("source_note", sa.String(length=500), nullable=True),
        sa.Column("updated_by", sa.String(length=255), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint(
            "tenant_id", "cap_year", name="uq_hospice_cap_record_tenant_year"
        ),
    )
    op.create_index(
        "ix_hospice_cap_records_tenant_id", "hospice_cap_records", ["tenant_id"]
    )
    op.create_index(
        "ix_hospice_cap_records_tenant_year",
        "hospice_cap_records",
        ["tenant_id", "cap_year"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_hospice_cap_records_tenant_year", table_name="hospice_cap_records"
    )
    op.drop_index(
        "ix_hospice_cap_records_tenant_id", table_name="hospice_cap_records"
    )
    op.drop_table("hospice_cap_records")
