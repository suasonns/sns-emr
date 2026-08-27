"""add bereavement_poc primary bereaved, risk provenance, other_interventions

Revision ID: e0f45baa4ec0
Revises: 99f2272f7253
Create Date: 2026-08-25

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "e0f45baa4ec0"
down_revision = "99f2272f7253"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("bereavement_pocs", sa.Column("risk_source", sa.String(16), nullable=True))
    op.add_column("bereavement_pocs", sa.Column("risk_score", sa.Integer(), nullable=True))

    op.add_column("bereavement_pocs", sa.Column("no_family", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("bereavement_pocs", sa.Column("primary_first_name", sa.String(128), nullable=True))
    op.add_column("bereavement_pocs", sa.Column("primary_last_name", sa.String(128), nullable=True))
    op.add_column("bereavement_pocs", sa.Column("primary_relationship_to_patient", sa.String(128), nullable=True))
    op.add_column("bereavement_pocs", sa.Column("primary_address", sa.String(255), nullable=True))
    op.add_column("bereavement_pocs", sa.Column("primary_city", sa.String(128), nullable=True))
    op.add_column("bereavement_pocs", sa.Column("primary_state", sa.String(64), nullable=True))
    op.add_column("bereavement_pocs", sa.Column("primary_zip", sa.String(16), nullable=True))
    op.add_column("bereavement_pocs", sa.Column("primary_home_phone", sa.String(32), nullable=True))
    op.add_column("bereavement_pocs", sa.Column("primary_cell_phone", sa.String(32), nullable=True))
    op.add_column("bereavement_pocs", sa.Column("primary_email", sa.String(255), nullable=True))
    op.add_column("bereavement_pocs", sa.Column("primary_was_caregiver", sa.Boolean(), nullable=True))

    op.add_column("bereavement_pocs", sa.Column("other_interventions", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("bereavement_pocs", "other_interventions")

    op.drop_column("bereavement_pocs", "primary_was_caregiver")
    op.drop_column("bereavement_pocs", "primary_email")
    op.drop_column("bereavement_pocs", "primary_cell_phone")
    op.drop_column("bereavement_pocs", "primary_home_phone")
    op.drop_column("bereavement_pocs", "primary_zip")
    op.drop_column("bereavement_pocs", "primary_state")
    op.drop_column("bereavement_pocs", "primary_city")
    op.drop_column("bereavement_pocs", "primary_address")
    op.drop_column("bereavement_pocs", "primary_relationship_to_patient")
    op.drop_column("bereavement_pocs", "primary_last_name")
    op.drop_column("bereavement_pocs", "primary_first_name")
    op.drop_column("bereavement_pocs", "no_family")

    op.drop_column("bereavement_pocs", "risk_score")
    op.drop_column("bereavement_pocs", "risk_source")
