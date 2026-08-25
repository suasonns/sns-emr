"""add election_addendum_requests table

Revision ID: ab93ea51d692
Revises: 9a8c04c006b3
Create Date: 2026-08-26

Real tracking for the CMS Hospice Election Statement Addendum (42 CFR
418.24(b)) request/delivery timeliness rule -- see
app/billing/services/election_addendum_service.py.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "ab93ea51d692"
down_revision = "9a8c04c006b3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "election_addendum_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "patient_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("patients.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("requested_date", sa.Date(), nullable=False),
        sa.Column("requested_by", sa.String(length=32), nullable=False),
        sa.Column("delivered_date", sa.Date(), nullable=True),
        sa.Column("not_required_reason", sa.String(length=255), nullable=True),
        sa.Column("created_by", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index(
        "ix_election_addendum_requests_tenant_id", "election_addendum_requests", ["tenant_id"]
    )
    op.create_index(
        "ix_election_addendum_requests_patient_id", "election_addendum_requests", ["patient_id"]
    )
    op.create_index(
        "ix_election_addendum_requests_tenant_patient",
        "election_addendum_requests",
        ["tenant_id", "patient_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_election_addendum_requests_tenant_patient", table_name="election_addendum_requests")
    op.drop_index("ix_election_addendum_requests_patient_id", table_name="election_addendum_requests")
    op.drop_index("ix_election_addendum_requests_tenant_id", table_name="election_addendum_requests")
    op.drop_table("election_addendum_requests")
