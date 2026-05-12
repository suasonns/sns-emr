from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "343bbcfaebc3"
down_revision: Union[str, Sequence[str], None] = "435a3eb45748"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add benefit_period_id to idg_reviews to align DB schema with SQLAlchemy model.
    Nullable=True is intentional to avoid breaking existing rows.
    """
    op.add_column(
        "idg_reviews",
        sa.Column(
            "benefit_period_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )

    op.create_foreign_key(
        "fk_idg_reviews_benefit_period_id",
        source_table="idg_reviews",
        referent_table="benefit_periods",
        local_cols=["benefit_period_id"],
        remote_cols=["id"],
        ondelete="SET NULL",
    )

    op.create_index(
        "ix_idg_reviews_benefit_period_id",
        "idg_reviews",
        ["benefit_period_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_idg_reviews_benefit_period_id", table_name="idg_reviews")
    op.drop_constraint("fk_idg_reviews_benefit_period_id", "idg_reviews", type_="foreignkey")
    op.drop_column("idg_reviews", "benefit_period_id")
