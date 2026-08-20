"""extend patient pos history fields and physician contact fields

Revision ID: f2a4c0d9e1b7
Revises: c93f61a20d75
Create Date: 2026-08-18
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "f2a4c0d9e1b7"
down_revision: Union[str, Sequence[str], None] = "c93f61a20d75"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("patient_pos", sa.Column("pos_address", sa.String(length=255), nullable=True))
    op.add_column("patient_pos", sa.Column("room_number", sa.String(length=64), nullable=True))
    op.add_column("patient_pos", sa.Column("notes", sa.Text(), nullable=True))
    op.add_column("patient_pos", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("patient_pos", sa.Column("updated_by", sa.String(length=255), nullable=True))
    op.add_column("patient_facesheet", sa.Column("attending_physician_address", sa.String(length=255), nullable=True))
    op.add_column("patient_facesheet", sa.Column("attending_physician_phone", sa.String(length=255), nullable=True))
    op.add_column("patient_facesheet", sa.Column("attending_physician_fax", sa.String(length=255), nullable=True))
    op.add_column("patient_facesheet", sa.Column("medical_director_address", sa.String(length=255), nullable=True))
    op.add_column("patient_facesheet", sa.Column("medical_director_phone", sa.String(length=255), nullable=True))
    op.add_column("patient_facesheet", sa.Column("medical_director_fax", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("patient_facesheet", "medical_director_fax")
    op.drop_column("patient_facesheet", "medical_director_address")
    op.drop_column("patient_facesheet", "attending_physician_fax")
    op.drop_column("patient_facesheet", "attending_physician_phone")
    op.drop_column("patient_facesheet", "attending_physician_address")
    op.drop_column("patient_facesheet", "medical_director_phone")
    op.drop_column("patient_pos", "updated_by")
    op.drop_column("patient_pos", "updated_at")
    op.drop_column("patient_pos", "notes")
    op.drop_column("patient_pos", "room_number")
    op.drop_column("patient_pos", "pos_address")
