from alembic import op

# revision identifiers, used by Alembic.
revision = "c6eb02e21077"
down_revision = "73ad350a8be4"
branch_labels = None
depends_on = None


def upgrade():
    # 1) Rename primary key column id -> idg_id (forward-safe)
    op.execute("""
    DO $$
    BEGIN
        IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema='public'
              AND table_name='idg_meetings'
              AND column_name='id'
        )
        AND NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema='public'
              AND table_name='idg_meetings'
              AND column_name='idg_id'
        )
        THEN
            ALTER TABLE idg_meetings RENAME COLUMN id TO idg_id;
        END IF;
    END $$;
    """)

    # 2) Ensure enum exists
    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_type WHERE typname = 'idg_status_enum'
        )
        THEN
            CREATE TYPE idg_status_enum AS ENUM (
                'SCHEDULED',
                'IN_PROGRESS',
                'COMPLETED'
            );
        END IF;
    END $$;
    """)

    # 3) Convert status column from varchar -> enum safely (handle defaults)
    op.execute("""
    DO $$
    BEGIN
        IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema='public'
              AND table_name='idg_meetings'
              AND column_name='status'
              AND data_type='character varying'
        )
        THEN
            -- Drop default first (prevents DatatypeMismatch)
            ALTER TABLE idg_meetings ALTER COLUMN status DROP DEFAULT;

            -- Normalize existing values
            UPDATE idg_meetings
            SET status = CASE
                WHEN upper(status) IN ('DRAFT','SCHEDULED') THEN 'SCHEDULED'
                WHEN upper(status) IN ('IN_PROGRESS','INPROGRESS') THEN 'IN_PROGRESS'
                WHEN upper(status) IN ('COMPLETED','FINALIZED') THEN 'COMPLETED'
                ELSE 'SCHEDULED'
            END;

            -- Convert column type to enum
            ALTER TABLE idg_meetings
            ALTER COLUMN status
            TYPE idg_status_enum
            USING status::idg_status_enum;

            -- Set a valid enum default after conversion
            ALTER TABLE idg_meetings ALTER COLUMN status SET DEFAULT 'SCHEDULED';
        END IF;
    END $$;
    """)


def downgrade():
    # Forward-only safety: do not revert schema alignment
    pass
