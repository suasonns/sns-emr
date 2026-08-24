"""add ssn lookup hash to users

Adds ssn_lookup_hash: a deterministic HMAC-SHA256 of the normalized SSN
(see app/core/crypto.ssn_lookup_hash). ssn_encrypted (Fernet) is
randomized per encryption and can never be compared across rows, so this
indexed hash is what powers "find other User rows across tenants that
belong to the same physical person" for the cross-agency account-linking
feature (same person, different email/password per agency, discovered via
SSN match with name+DOB+license as corroboration).

Revision ID: e7f8a9b0c1d2
Revises: d6e7f8a9b0c1
Create Date: 2026-08-24 09:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "e7f8a9b0c1d2"
down_revision = "d6e7f8a9b0c1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("ssn_lookup_hash", sa.String(64), nullable=True))
    op.create_index("ix_users_ssn_lookup_hash", "users", ["ssn_lookup_hash"])


def downgrade() -> None:
    op.drop_index("ix_users_ssn_lookup_hash", table_name="users")
    op.drop_column("users", "ssn_lookup_hash")
