"""reconcile model/schema drift (pre-existing, unrelated to RNICA)

Revision ID: cd6205fb97e3
Revises: c2a3b4d5e6f7
Create Date: 2026-08-28 23:35:00.000000

Closes the gap surfaced by the CI "schema matches models" drift probe.
Most of the probe's diff was models that never declared a server_default,
index, or unique constraint that the DB already had from an earlier
migration -- fixed by updating the models to match the DB (no schema
change; see the accompanying model edits in this commit). The
claim_edi_batches.batch_number and visit_recordings.client_recording_id
duplicate constraint+index pairs were handled the same way (declared in
the model to match reality) rather than dropped, since this repo's
migration safety guard blocks `op.drop_index`/`op.drop_column`/
`op.drop_table` in upgrade() and neither pair is actually harmful.

The one item that genuinely needed a schema change: patient_issues.tenant_id
has been declared as a ForeignKey in the model since the table was
introduced, but no migration ever created the actual FK constraint in
Postgres. Verified zero orphaned tenant_id rows in the shared dev DB
before adding it here.
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'cd6205fb97e3'
down_revision: Union[str, Sequence[str], None] = 'c2a3b4d5e6f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_foreign_key(
        op.f("fk_patient_issues_tenant_id_tenants"),
        "patient_issues",
        "tenants",
        ["tenant_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("fk_patient_issues_tenant_id_tenants"),
        "patient_issues",
        type_="foreignkey",
    )
