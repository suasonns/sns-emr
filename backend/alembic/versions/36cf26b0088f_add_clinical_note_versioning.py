"""add clinical note versioning

Revision ID: 36cf26b0088f
Revises: 4ed222ffed27
Create Date: 2026-06-16

SNS EMR clinical note versioning migration.

Purpose:
- Keep clinical_notes as the stable note container
- Add clinical_note_versions for immutable note history
- Add current_version_id pointer on clinical_notes
- Enforce exactly one active version per clinical note

IMPORTANT:
- This migration is safe to run without assuming legacy content column names.
- Backfill of existing clinical_notes rows into version 1 must be enabled
  only after verifying the real legacy columns in clinical_notes.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "36cf26b0088f"
down_revision = "4ed222ffed27"
branch_labels = None
depends_on = None


def upgrade():
    # 1) Create version table
    op.create_table(
        "clinical_note_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("clinical_note_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("amend_reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.PrimaryKeyConstraint("id", name="pk_clinical_note_versions"),
        sa.ForeignKeyConstraint(
            ["clinical_note_id"],
            ["clinical_notes.id"],
            name="fk_clinical_note_versions_clinical_note_id",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "clinical_note_id",
            "version_number",
            name="uq_clinical_note_versions_note_version",
        ),
        sa.CheckConstraint(
            "version_number >= 1",
            name="ck_clinical_note_versions_version_number_positive",
        ),
    )

    # 2) Add pointer to active version on container table
    op.add_column(
        "clinical_notes",
        sa.Column("current_version_id", postgresql.UUID(as_uuid=True), nullable=True),
    )

    # 3) Add pointer foreign key after target table exists
    op.create_foreign_key(
        "fk_clinical_notes_current_version_id",
        "clinical_notes",
        "clinical_note_versions",
        ["current_version_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    # 4) Indexes for lookup and integrity
    op.create_index(
        "ix_clinical_note_versions_clinical_note_id",
        "clinical_note_versions",
        ["clinical_note_id"],
        unique=False,
    )

    op.create_index(
        "ix_clinical_note_versions_note_active",
        "clinical_note_versions",
        ["clinical_note_id", "is_active"],
        unique=False,
    )

    op.create_index(
        "uq_clinical_note_one_active_version",
        "clinical_note_versions",
        ["clinical_note_id"],
        unique=True,
        postgresql_where=sa.text("is_active = true"),
    )

    # ------------------------------------------------------------------
    # OPTIONAL BACKFILL (DO NOT ENABLE UNTIL LEGACY COLUMNS ARE VERIFIED)
    # ------------------------------------------------------------------
    # Replace the placeholder column names below with the real legacy
    # column names from clinical_notes before uncommenting.
    #
    # Example expected placeholders:
    # - LEGACY_CONTENT_COL
    # - LEGACY_CREATED_AT_COL
    # - LEGACY_CREATED_BY_COL
    #
    # op.execute(sa.text(\"\"\"
    #     INSERT INTO clinical_note_versions (
    #         id,
    #         clinical_note_id,
    #         version_number,
    #         content,
    #         amend_reason,
    #         created_at,
    #         created_by,
    #         is_active
    #     )
    #     SELECT
    #         gen_random_uuid(),
    #         id,
    #         1,
    #         LEGACY_CONTENT_COL,
    #         NULL,
    #         COALESCE(LEGACY_CREATED_AT_COL, now()),
    #         LEGACY_CREATED_BY_COL,
    #         true
    #     FROM clinical_notes
    # \"\"\"))
    #
    # op.execute(sa.text(\"\"\"
    #     UPDATE clinical_notes cn
    #     SET current_version_id = cnv.id
    #     FROM clinical_note_versions cnv
    #     WHERE cnv.clinical_note_id = cn.id
    #       AND cnv.version_number = 1
    # \"\"\"))


def downgrade():
    op.drop_constraint(
        "fk_clinical_notes_current_version_id",
        "clinical_notes",
        type_="foreignkey",
    )

    op.drop_index(
        "uq_clinical_note_one_active_version",
        table_name="clinical_note_versions",
    )

    op.drop_index(
        "ix_clinical_note_versions_note_active",
        table_name="clinical_note_versions",
    )

    op.drop_index(
        "ix_clinical_note_versions_clinical_note_id",
        table_name="clinical_note_versions",
    )

    op.drop_column("clinical_notes", "current_version_id")

    op.drop_table("clinical_note_versions")
