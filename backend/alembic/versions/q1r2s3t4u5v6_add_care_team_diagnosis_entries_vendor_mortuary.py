"""add care team, diagnosis entries, oxygen vendor, mortuary detail fields

Revision ID: q1r2s3t4u5v6
Revises: p7q8r9s0t1u2
Create Date: 2026-08-21 10:24:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "q1r2s3t4u5v6"
down_revision = "p7q8r9s0t1u2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("patient_facesheet", sa.Column("diagnosis_entries", sa.JSON(), nullable=True))

    op.add_column("patient_facesheet", sa.Column("lvn_name", sa.String(), nullable=True))
    op.add_column("patient_facesheet", sa.Column("chaplain_name", sa.String(), nullable=True))
    op.add_column("patient_facesheet", sa.Column("chha_name", sa.String(), nullable=True))
    op.add_column("patient_facesheet", sa.Column("volunteer_name", sa.String(), nullable=True))
    op.add_column("patient_facesheet", sa.Column("clinical_manager_name", sa.String(), nullable=True))

    op.add_column("patient_facesheet", sa.Column("oxygen_vendor_name", sa.String(), nullable=True))
    op.add_column("patient_facesheet", sa.Column("oxygen_vendor_phone", sa.String(), nullable=True))
    op.add_column("patient_facesheet", sa.Column("oxygen_vendor_emergency_phone", sa.String(), nullable=True))

    op.add_column("patient_facesheet", sa.Column("mortuary_prearranged", sa.Boolean(), nullable=True))
    op.add_column("patient_facesheet", sa.Column("mortuary_contact_name", sa.String(), nullable=True))
    op.add_column("patient_facesheet", sa.Column("mortuary_contact_phone", sa.String(), nullable=True))
    op.add_column("patient_facesheet", sa.Column("mortuary_notes", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("patient_facesheet", "mortuary_notes")
    op.drop_column("patient_facesheet", "mortuary_contact_phone")
    op.drop_column("patient_facesheet", "mortuary_contact_name")
    op.drop_column("patient_facesheet", "mortuary_prearranged")

    op.drop_column("patient_facesheet", "oxygen_vendor_emergency_phone")
    op.drop_column("patient_facesheet", "oxygen_vendor_phone")
    op.drop_column("patient_facesheet", "oxygen_vendor_name")

    op.drop_column("patient_facesheet", "clinical_manager_name")
    op.drop_column("patient_facesheet", "volunteer_name")
    op.drop_column("patient_facesheet", "chha_name")
    op.drop_column("patient_facesheet", "chaplain_name")
    op.drop_column("patient_facesheet", "lvn_name")

    op.drop_column("patient_facesheet", "diagnosis_entries")
