"""add_bereavement_assessments_table

Revision ID: 39a3ecfb64ad
Revises: c1471f28885b
Create Date: 2026-08-25 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '39a3ecfb64ad'
down_revision: Union[str, Sequence[str], None] = 'c1471f28885b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "bereavement_assessments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("status", sa.String(16), nullable=False, server_default=sa.text("'DRAFT'"), index=True),
        sa.Column("entered_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("staff_assigned", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("discipline", sa.String(16), nullable=True),
        sa.Column("care_level", sa.String(16), nullable=True),
        sa.Column("visit_type", sa.String(16), nullable=True),
        sa.Column("visit_mode", sa.String(16), nullable=True),
        sa.Column("visit_date", sa.Date(), nullable=True),
        sa.Column("time_in", sa.String(8), nullable=True),
        sa.Column("time_out", sa.String(8), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("no_family", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("primary_first_name", sa.String(128), nullable=True),
        sa.Column("primary_last_name", sa.String(128), nullable=True),
        sa.Column("primary_age", sa.Integer(), nullable=True),
        sa.Column("primary_gender", sa.String(32), nullable=True),
        sa.Column("primary_address", sa.String(255), nullable=True),
        sa.Column("primary_city", sa.String(128), nullable=True),
        sa.Column("primary_state", sa.String(64), nullable=True),
        sa.Column("primary_zip", sa.String(16), nullable=True),
        sa.Column("primary_home_phone", sa.String(32), nullable=True),
        sa.Column("primary_work_phone", sa.String(32), nullable=True),
        sa.Column("primary_cell_phone", sa.String(32), nullable=True),
        sa.Column("primary_email", sa.String(255), nullable=True),
        sa.Column("primary_relationship_to_patient", sa.String(128), nullable=True),
        sa.Column("primary_was_caregiver", sa.Boolean(), nullable=True),
        sa.Column("risk_items", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("risk_other_note", sa.Text(), nullable=True),
        sa.Column("risk_total_score", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("risk_level", sa.String(16), nullable=True),
        sa.Column("additional_bereaved", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("narrative", sa.Text(), nullable=True),
        sa.Column("signed_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("signed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("bereavement_assessments")
