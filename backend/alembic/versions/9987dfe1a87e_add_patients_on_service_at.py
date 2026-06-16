"""add patients on_service_at

Revision ID: 9987dfe1a87e
Revises: 928c5ccdb04e
Create Date: 2026-06-01

Adds a nullable SOC timestamp field. No behavior change.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "9987dfe1a87e"
down_revision = "928c5ccdb04e"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "patients",
        sa.Column("on_service_at", sa.DateTime(timezone=True), nullable=True),
        schema="public",
    )


def downgrade():
    op.drop_column("patients", "on_service_at", schema="public")
