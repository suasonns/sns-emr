from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text


def main() -> int:
    base_dir = Path(__file__).resolve().parents[1]
    load_dotenv(base_dir / '.env.local', override=False)
    load_dotenv(base_dir / '.env', override=False)

    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise RuntimeError('DATABASE_URL is not set. Refusing to run without DB config.')

    engine = create_engine(database_url, future=True)
    with engine.begin() as conn:
        rogue_patient_ids = conn.execute(
            text(
                """
                SELECT id
                FROM patients
                WHERE patient_type IN ('TRAINING', 'DEMO', 'TEST')
                   OR training_label = 'SYNTHETIC TEST DATA'
                   OR mrn LIKE 'TEST-%'
                ORDER BY id
                """
            )
        ).fetchall()

        rogue_ids = [str(row[0]) for row in rogue_patient_ids]
        print(f"dummy patient rows found: {len(rogue_ids)}")

        if not rogue_ids:
            print('No dummy patient rows to remove.')
            return 0

        child_tables = conn.execute(
            text(
                """
                SELECT DISTINCT conrelid::regclass::text AS child_table
                FROM pg_constraint c
                WHERE c.contype = 'f'
                  AND c.confrelid = 'patients'::regclass
                ORDER BY 1
                """
            )
        ).fetchall()

        for (child_table,) in child_tables:
            conn.execute(
                text(
                    f"DELETE FROM {child_table} WHERE patient_id::text = ANY(:patient_ids)"
                ),
                {'patient_ids': rogue_ids},
            )
            print(f"deleted rows from {child_table}")

        deleted = conn.execute(
            text(
                """
                DELETE FROM patients
                WHERE id::text = ANY(:patient_ids)
                """
            ),
            {'patient_ids': rogue_ids},
        )

        remaining = conn.execute(
            text(
                """
                SELECT COUNT(*)
                FROM patients
                WHERE patient_type IN ('TRAINING', 'DEMO', 'TEST')
                   OR training_label = 'SYNTHETIC TEST DATA'
                   OR mrn LIKE 'TEST-%'
                """
            )
        ).scalar_one()

        print(f"dummy patient rows removed: {deleted.rowcount}")
        print(f"dummy patient rows remaining: {remaining}")

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
