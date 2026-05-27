from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "c467b78906f9"
down_revision = "55edc63b30d2"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "assessment_discrepancies",
        sa.Column(
            "resolution_type",
            sa.String(length=30),
            nullable=True
        )
    )


def downgrade():
    op.drop_column(
        "assessment_discrepancies",
        "resolution_type"
    )