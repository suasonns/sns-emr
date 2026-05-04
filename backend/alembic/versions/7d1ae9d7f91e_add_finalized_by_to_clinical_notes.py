from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "7d1ae9d7f91e"
down_revision = "56a2b42ae284"   
branch_labels = None
depends_on = None

def upgrade():
    op.add_column(
        "clinical_notes",
        sa.Column("finalized_by", UUID(as_uuid=True), nullable=True),
    )

def downgrade():
    op.drop_column("clinical_notes", "finalized_by")