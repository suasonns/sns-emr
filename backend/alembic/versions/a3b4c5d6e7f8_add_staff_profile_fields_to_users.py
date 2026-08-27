"""add staff profile fields to users

Adds the Personal Information / Professional Information / Access fields
needed for real Staff Management (Insights -> HR) to replace the mock
roster in AnalyticsHR.jsx. Scope intentionally excludes SSN (sensitive PII,
needs an encryption-at-rest plan before we store it), pay rate, and
license/document expiration tracking (owner directive: not needed yet).

Revision ID: a3b4c5d6e7f8
Revises: z2b3c4d5e6f7
Create Date: 2026-08-24 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "a3b4c5d6e7f8"
down_revision = "z2b3c4d5e6f7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        # Personal information
        batch_op.add_column(sa.Column("date_of_birth", sa.Date(), nullable=True))
        batch_op.add_column(sa.Column("address_street", sa.String(255), nullable=True))
        batch_op.add_column(sa.Column("address_city", sa.String(100), nullable=True))
        batch_op.add_column(sa.Column("address_state", sa.String(2), nullable=True))
        batch_op.add_column(sa.Column("address_zip", sa.String(10), nullable=True))
        batch_op.add_column(sa.Column("phone", sa.String(20), nullable=True))
        batch_op.add_column(sa.Column("home_phone", sa.String(20), nullable=True))

        # Professional information
        batch_op.add_column(sa.Column("job_title", sa.String(150), nullable=True))
        batch_op.add_column(sa.Column("discipline", sa.String(50), nullable=True))
        batch_op.add_column(sa.Column("npi", sa.String(10), nullable=True))
        batch_op.add_column(sa.Column("employment_date", sa.Date(), nullable=True))
        batch_op.add_column(sa.Column("employment_end_date", sa.Date(), nullable=True))

        # Access / account setting
        batch_op.add_column(
            sa.Column("staff_type", sa.String(1), nullable=True)
        )  # C=Clinical, A=Administrative, X=Contracted, Y=Referral Source


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("staff_type")
        batch_op.drop_column("employment_end_date")
        batch_op.drop_column("employment_date")
        batch_op.drop_column("npi")
        batch_op.drop_column("discipline")
        batch_op.drop_column("job_title")
        batch_op.drop_column("home_phone")
        batch_op.drop_column("phone")
        batch_op.drop_column("address_zip")
        batch_op.drop_column("address_state")
        batch_op.drop_column("address_city")
        batch_op.drop_column("address_street")
        batch_op.drop_column("date_of_birth")
