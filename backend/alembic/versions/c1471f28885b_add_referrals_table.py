"""add_referrals_table

Revision ID: c1471f28885b
Revises: d7c72f3a34c9
Create Date: 2026-08-25 14:35:36.630664

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c1471f28885b'
down_revision: Union[str, Sequence[str], None] = 'd7c72f3a34c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "referrals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("status", sa.String(32), nullable=False, server_default=sa.text("'PENDING'")),
        sa.Column("first_name", sa.String(128), nullable=False),
        sa.Column("middle_name", sa.String(128), nullable=True),
        sa.Column("last_name", sa.String(128), nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=False),
        sa.Column("phone", sa.String(32), nullable=True),
        sa.Column("address", sa.String(255), nullable=True),
        sa.Column("city", sa.String(128), nullable=True),
        sa.Column("state", sa.String(64), nullable=True),
        sa.Column("zip", sa.String(16), nullable=True),
        sa.Column("gender", sa.String(32), nullable=True),
        sa.Column("language", sa.String(64), nullable=True),
        sa.Column("religion", sa.String(64), nullable=True),
        sa.Column("marital_status", sa.String(64), nullable=True),
        sa.Column("primary_payer", sa.String(128), nullable=True),
        sa.Column("primary_policy_number", sa.String(128), nullable=True),
        sa.Column("authorization_status", sa.String(64), nullable=True),
        sa.Column("current_level_of_care", sa.String(64), nullable=True),
        sa.Column("primary_diagnosis", sa.String(255), nullable=True),
        sa.Column("secondary_diagnoses", sa.Text(), nullable=True),
        sa.Column("attending_physician_name", sa.String(255), nullable=True),
        sa.Column("attending_physician_npi", sa.String(32), nullable=True),
        sa.Column("referral_source", sa.String(255), nullable=True),
        sa.Column("referral_date", sa.Date(), nullable=True),
        sa.Column("special_instructions", sa.Text(), nullable=True),
        sa.Column("responsible_party_name", sa.String(255), nullable=True),
        sa.Column("responsible_party_relationship", sa.String(128), nullable=True),
        sa.Column("responsible_party_phone", sa.String(32), nullable=True),
        sa.Column("emergency_contact_name", sa.String(255), nullable=True),
        sa.Column("emergency_contact_relationship", sa.String(128), nullable=True),
        sa.Column("emergency_contact_phone", sa.String(32), nullable=True),
        sa.Column("decline_reason", sa.Text(), nullable=True),
        sa.Column("converted_patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patients.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_referrals_status", "referrals", ["status"])


def downgrade() -> None:
    """Downgrade schema."""
    pass

