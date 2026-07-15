from app.db.session import SessionLocal
from sqlalchemy import text

db = SessionLocal()

try:
    total = db.execute(
        text("SELECT COUNT(*) FROM icd10_master")
    ).scalar()

    dotted = db.execute(
        text("""
            SELECT COUNT(*)
            FROM icd10_master
            WHERE icd10_code LIKE '%.%'
        """)
    ).scalar()

    duplicates = db.execute(
        text("""
            SELECT COUNT(*)
            FROM (
                SELECT
                    upper(
                        replace(
                            replace(icd10_code,'.',''),
                            ' ',
                            ''
                        )
                    ) AS normalized_code
                FROM icd10_master
                GROUP BY normalized_code
                HAVING COUNT(*) > 1
            ) t
        """)
    ).scalar()

    print("=" * 50)
    print("ICD10 IMPORT AUDIT")
    print("=" * 50)

    print("TOTAL ICD CODES :", total)
    print("DOTTED CODES    :", dotted)
    print("DUPLICATES      :", duplicates)

finally:
    db.close()