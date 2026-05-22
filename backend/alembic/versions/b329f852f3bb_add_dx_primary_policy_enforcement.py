"""add_dx_primary_policy_enforcement

Revision ID: b329f852f3bb
Revises: b0d8818c0547
Create Date: 2026-05-20 16:14:21.746312
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = "b329f852f3bb"
down_revision: Union[str, Sequence[str], None] = "b0d8818c0547"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Enterprise-grade adaptive repair migration.

    Handles multiple historical variants of dx_primary_policy safely.
    Does NOT assume operator / allow_secondary columns exist.
    """

    bind = op.get_bind()
    inspector = inspect(bind)

    if not inspector.has_table("dx_primary_policy"):
        raise RuntimeError(
            "dx_primary_policy table does not exist. "
            "This migration assumes a legacy policy table."
        )

    cols = {c["name"] for c in inspector.get_columns("dx_primary_policy")}

    has_operator = "operator" in cols
    has_allow_secondary = "allow_secondary" in cols

    # Build INSERT dynamically based on existing columns
    if has_operator and has_allow_secondary:
        insert_sql = """
        INSERT INTO dx_primary_policy (
            id,
            tenant_id,
            code_pattern,
            operator,
            allow_primary,
            allow_secondary,
            reason
        )
        SELECT
            gen_random_uuid(),
            t.id,
            p.code_pattern,
            'LIKE',
            FALSE,
            TRUE,
            p.reason
        FROM tenants t
        CROSS JOIN (
            VALUES
                ('F%', 'Mental/behavioral codes not allowed as hospice primary dx'),
                ('R%', 'Signs/symptoms not allowed as hospice primary dx'),
                ('V%', 'External cause codes not allowed as hospice primary dx'),
                ('W%', 'External cause codes not allowed as hospice primary dx'),
                ('X%', 'External cause codes not allowed as hospice primary dx'),
                ('Y%', 'External cause codes not allowed as hospice primary dx'),
                ('Z%', 'Encounter/status Z codes not allowed as hospice primary dx')
        ) AS p(code_pattern, reason)
        ON CONFLICT DO NOTHING;
        """
    else:
        # Minimal guaranteed schema
        insert_sql = """
        INSERT INTO dx_primary_policy (
            id,
            tenant_id,
            code_pattern,
            allow_primary,
            reason
        )
        SELECT
            gen_random_uuid(),
            t.id,
            p.code_pattern,
            FALSE,
            p.reason
        FROM tenants t
        CROSS JOIN (
            VALUES
                ('F%', 'Mental/behavioral codes not allowed as hospice primary dx'),
                ('R%', 'Signs/symptoms not allowed as hospice primary dx'),
                ('V%', 'External cause codes not allowed as hospice primary dx'),
                ('W%', 'External cause codes not allowed as hospice primary dx'),
                ('X%', 'External cause codes not allowed as hospice primary dx'),
                ('Y%', 'External cause codes not allowed as hospice primary dx'),
                ('Z%', 'Encounter/status Z codes not allowed as hospice primary dx')
        ) AS p(code_pattern, reason)
        ON CONFLICT DO NOTHING;
        """

    op.execute(insert_sql)


def downgrade() -> None:
    # Forward-only by design (compliance enforcement migration)
    pass