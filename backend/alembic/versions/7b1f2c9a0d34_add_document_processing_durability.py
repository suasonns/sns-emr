"""add document processing durability, idempotency, and retry tracking

Revision ID: 7b1f2c9a0d34
Revises: b6c7d8e9f0a1
Create Date: 2026-08-28 11:40:00.000000

Phase A of the offline-durability initiative: guarantees that a document
uploaded while an RN has connectivity for only a moment (upload succeeds,
but AI extraction/harvest is later delayed, interrupted by a server
restart, or fails transiently) is never silently dropped -- it stays
recoverable and reprocessable, exactly once, until it truly completes.

Adds to document_records:
    - processing_status: PENDING -> PROCESSING -> COMPLETE | FAILED
      state machine for the document-intelligence + harvest pipeline.
    - content_hash: sha256 of the uploaded bytes, scoped per
      (tenant_id, patient_id). Lets the upload endpoint recognize a
      byte-identical re-upload (e.g. an RN's app retried an upload that
      it wasn't sure succeeded after a connectivity drop) and treat it
      as the SAME document instead of creating a duplicate that would
      harvest duplicate structured findings.
    - processing_attempts / last_processing_error / processing_started_at
      / processing_completed_at: retry-queue bookkeeping so a recovery
      sweep can find stuck/failed documents and safely re-drive them,
      and so support/ops has audit visibility into what happened.

Adds a unique constraint to patient_evidence_records on
(tenant_id, source_type, source_record_id) so harvest_from_source can
never create two evidence records (and therefore never two sets of
harvested signals / structured findings) for the same source document,
even if the recovery sweep and a live request race to reprocess it.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7b1f2c9a0d34'
down_revision: Union[str, Sequence[str], None] = 'b6c7d8e9f0a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "document_records",
        sa.Column(
            "processing_status",
            sa.String(length=24),
            nullable=False,
            server_default=sa.text("'PENDING'"),
        ),
    )
    op.add_column(
        "document_records",
        sa.Column("content_hash", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "document_records",
        sa.Column(
            "processing_attempts",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.add_column(
        "document_records",
        sa.Column("last_processing_error", sa.Text(), nullable=True),
    )
    op.add_column(
        "document_records",
        sa.Column("processing_started_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "document_records",
        sa.Column("processing_completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_index(
        "ix_document_records_processing_status",
        "document_records",
        ["processing_status"],
    )
    op.create_index(
        "ix_document_records_patient_content_hash",
        "document_records",
        ["patient_id", "content_hash"],
    )

    # Existing rows (uploaded before this migration) already have their
    # text/AI extraction outcome recorded on document_text/extracted_values
    # (or not, if it never ran) -- backfill them to COMPLETE so the
    # recovery sweep does not immediately try to reprocess the entire
    # historical document archive.
    op.execute(
        """
        UPDATE document_records
        SET processing_status = 'COMPLETE',
            processing_completed_at = COALESCE(updated_at, uploaded_at)
        WHERE document_text IS NOT NULL AND document_text <> ''
        """
    )

    op.create_unique_constraint(
        "uq_evidence_records_tenant_source",
        "patient_evidence_records",
        ["tenant_id", "source_type", "source_record_id"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "uq_evidence_records_tenant_source",
        "patient_evidence_records",
        type_="unique",
    )
    op.drop_index("ix_document_records_patient_content_hash", table_name="document_records")
    op.drop_index("ix_document_records_processing_status", table_name="document_records")
    op.drop_column("document_records", "processing_completed_at")
    op.drop_column("document_records", "processing_started_at")
    op.drop_column("document_records", "last_processing_error")
    op.drop_column("document_records", "processing_attempts")
    op.drop_column("document_records", "content_hash")
    op.drop_column("document_records", "processing_status")
