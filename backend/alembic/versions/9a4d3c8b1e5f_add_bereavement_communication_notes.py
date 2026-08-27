"""add bereavement_communication_notes table

Revision ID: 9a4d3c8b1e5f
Revises: 7b2f4e9a1c6d
Create Date: 2026-08-25 16:30:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "9a4d3c8b1e5f"
down_revision = "7b2f4e9a1c6d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "bereavement_communication_notes",
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
            "bereavement_letter_tracker_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("bereavement_letter_trackers.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("contact_date", sa.Date(), nullable=False),
        sa.Column("contact_type", sa.String(length=16), nullable=False),
        sa.Column("contact_with", sa.String(length=255), nullable=True),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_bereavement_communication_notes_tenant_id",
        "bereavement_communication_notes",
        ["tenant_id"],
    )
    op.create_index(
        "ix_bereavement_communication_notes_patient_id",
        "bereavement_communication_notes",
        ["patient_id"],
    )
    op.create_index(
        "ix_bereavement_communication_notes_contact_date",
        "bereavement_communication_notes",
        ["contact_date"],
    )
    op.create_index(
        "ix_bereavement_communication_notes_tracker_id",
        "bereavement_communication_notes",
        ["bereavement_letter_tracker_id"],
    )
    op.create_index(
        "ix_bereavement_communication_notes_patient_date",
        "bereavement_communication_notes",
        ["patient_id", "contact_date"],
    )


def downgrade() -> None:
    op.drop_index("ix_bereavement_communication_notes_patient_date", table_name="bereavement_communication_notes")
    op.drop_index("ix_bereavement_communication_notes_tracker_id", table_name="bereavement_communication_notes")
    op.drop_index("ix_bereavement_communication_notes_contact_date", table_name="bereavement_communication_notes")
    op.drop_index("ix_bereavement_communication_notes_patient_id", table_name="bereavement_communication_notes")
    op.drop_index("ix_bereavement_communication_notes_tenant_id", table_name="bereavement_communication_notes")
    op.drop_table("bereavement_communication_notes")
