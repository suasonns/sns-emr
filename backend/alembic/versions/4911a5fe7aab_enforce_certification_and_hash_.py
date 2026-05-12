"""enforce_certification_and_hash_requirements

Revision ID: 4911a5fe7aab
Revises: 2bae706344b5
Create Date: 2026-05-05 19:48:28.067349
"""

from alembic import op

revision = "4911a5fe7aab"
down_revision = "2bae706344b5"
branch_labels = None
depends_on = None


def upgrade():
    # 0) Needed for digest()/sha256 hashing
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")

    # 1) Temporarily disable the header immutability trigger so we can repair legacy rows
    # (You already locked a report earlier for testing, and LOCKED blocks updates)
    op.execute("""
    ALTER TABLE regulatory_reports
    DISABLE TRIGGER trg_block_report_update_when_locked;
    """)

    # 2) Backfill certified_at for any CERTIFIED/LOCKED rows missing it
    op.execute("""
    UPDATE regulatory_reports
    SET certified_at = COALESCE(certified_at, generated_at, now())
    WHERE status IN ('CERTIFIED', 'LOCKED')
      AND certified_at IS NULL;
    """)

    # 3) Backfill integrity_hash for any LOCKED rows missing it (deterministic SHA-256)
    # Hash includes: header + ordered metrics (stable order)
    op.execute("""
    UPDATE regulatory_reports r
    SET integrity_hash = encode(
        digest(
            concat_ws('|',
                r.id::text,
                r.report_type::text,
                r.period_start::text,
                r.period_end::text,
                r.status::text,
                COALESCE((
                    SELECT string_agg(
                        concat_ws('|',
                            COALESCE(m.section_id::text, ''),
                            m.metric_key,
                            COALESCE(m.metric_value_numeric::text, ''),
                            COALESCE(m.metric_value_text, ''),
                            COALESCE(m.breakdown_json::text, '')
                        ),
                        '||'
                        ORDER BY m.section_id NULLS LAST, m.metric_key
                    )
                    FROM regulatory_report_metrics m
                    WHERE m.report_id = r.id
                ), '')
            ),
            'sha256'
        ),
        'hex'
    )
    WHERE r.status = 'LOCKED'
      AND r.integrity_hash IS NULL;
    """)

    # 4) Re-enable immutability trigger
    op.execute("""
    ALTER TABLE regulatory_reports
    ENABLE TRIGGER trg_block_report_update_when_locked;
    """)

    # 5) Now add constraints safely (no rows should violate them)
    op.execute("""
    ALTER TABLE regulatory_reports
    ADD CONSTRAINT chk_certified_requires_certified_at
    CHECK (
        status NOT IN ('CERTIFIED', 'LOCKED')
        OR certified_at IS NOT NULL
    );
    """)

    op.execute("""
    ALTER TABLE regulatory_reports
    ADD CONSTRAINT chk_locked_requires_integrity_hash
    CHECK (
        status <> 'LOCKED'
        OR integrity_hash IS NOT NULL
    );
    """)


def downgrade():
    op.execute("ALTER TABLE regulatory_reports DROP CONSTRAINT IF EXISTS chk_locked_requires_integrity_hash;")
    op.execute("ALTER TABLE regulatory_reports DROP CONSTRAINT IF EXISTS chk_certified_requires_certified_at;")
