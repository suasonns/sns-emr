"""add encrypted ssn fields to users

Adds field-level encrypted SSN storage: ssn_encrypted holds a Fernet
ciphertext (see app/core/crypto.py), ssn_last4 holds the plaintext last
4 digits only (industry-standard practice, like card-on-file last4) so
the roster can display a masked value without decrypting anything. The
full SSN is only ever decrypted by the admin-gated reveal endpoint,
which is audit-logged.

Revision ID: d6e7f8a9b0c1
Revises: c5d6e7f8a9b0
Create Date: 2026-08-23 17:10:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "d6e7f8a9b0c1"
down_revision = "c5d6e7f8a9b0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("ssn_encrypted", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("ssn_last4", sa.String(4), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "ssn_last4")
    op.drop_column("users", "ssn_encrypted")
