from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

from sqlalchemy import func, text
from sqlalchemy.dialects.postgresql import insert as pg_insert


# =========================================================
# PROJECT ROOT
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# =========================================================
# APPLICATION IMPORTS
# =========================================================

from app.db.session import SessionLocal
from app.models.icd10_master import ICD10Master


# =========================================================
# CONFIGURATION
# =========================================================

DEFAULT_CODES_FILE = (
    PROJECT_ROOT
    / "data"
    / "icd10"
    / "icd10cm-codes-2027.txt"
)

DEFAULT_EFFECTIVE_DATE = date(2026, 10, 1)
DEFAULT_BATCH_SIZE = 5000


# =========================================================
# CODES FILE PARSER
# =========================================================

CODES_LINE_PATTERN = re.compile(
    r"^([A-Z0-9]+)\s+(.+?)\s*$"
)


# =========================================================
# NORMALIZATION HELPERS
# =========================================================

def normalize_icd10_code(value):
    return (
        value
        .strip()
        .upper()
        .replace(".", "")
        .replace(" ", "")
    )


def dotted_icd10_code(value):
    code = normalize_icd10_code(value)

    if len(code) <= 3:
        return code

    return code[:3] + "." + code[3:]


def build_display_name(code, description):
    return (
        description.strip()
        + " ("
        + dotted_icd10_code(code)
        + ")"
    )


def build_search_text(code, description):
    compact_code = normalize_icd10_code(code)
    dotted_code = dotted_icd10_code(code)

    parts = [
        compact_code,
        dotted_code,
        description.strip(),
    ]

    return " ".join(
        part.lower()
        for part in parts
        if part and part.strip()
    )


def validate_lengths(code, description, display_name, line_number):
    if len(code) not in range(1, 21):
        raise ValueError(
            "Line "
            + str(line_number)
            + ": ICD10 code length is invalid: "
            + code
        )

    if len(description) not in range(1, 501):
        raise ValueError(
            "Line "
            + str(line_number)
            + ": diagnosis description length is invalid."
        )

    if len(display_name) not in range(1, 551):
        raise ValueError(
            "Line "
            + str(line_number)
            + ": display_name length is invalid."
        )


# =========================================================
# SOURCE ROW PARSING
# =========================================================

def parse_codes_line(line, line_number):
    stripped = line.strip()

    if not stripped:
        return None

    match = CODES_LINE_PATTERN.match(stripped)

    if not match:
        raise ValueError(
            "Line "
            + str(line_number)
            + ": unable to parse ICD10 codes file row: "
            + stripped
        )

    code = normalize_icd10_code(
        match.group(1)
    )

    description = (
        match.group(2)
        .strip()
    )

    if not code:
        raise ValueError(
            "Line "
            + str(line_number)
            + ": missing ICD10 code."
        )

    if not description:
        raise ValueError(
            "Line "
            + str(line_number)
            + ": missing diagnosis description."
        )

    display_name = build_display_name(
        code,
        description,
    )

    validate_lengths(
        code,
        description,
        display_name,
        line_number,
    )

    search_text = build_search_text(
        code,
        description,
    )

    return {
        "line_number": line_number,
        "icd10_code": code,
        "diagnosis_description": description,
        "display_name": display_name,
        "chapter_code": None,
        "chapter_name": None,
        "billable": True,
        "active": True,
        "effective_date": DEFAULT_EFFECTIVE_DATE,
        "retired_date": None,
        "search_text": search_text,
    }


def iter_source_rows(codes_file, stats, limit):
    seen_codes = set()

    with codes_file.open(
        "r",
        encoding="utf-8",
        errors="replace",
    ) as file:
        for line_number, line in enumerate(file, start=1):
            stats["source_lines"] += 1

            if not line.strip():
                stats["skipped_blank_lines"] += 1
                continue

            try:
                row = parse_codes_line(
                    line,
                    line_number,
                )
            except Exception:
                stats["parse_errors"] += 1
                raise

            if row is None:
                continue

            if row["icd10_code"] in seen_codes:
                stats["skipped_duplicate_source_codes"] += 1
                continue

            seen_codes.add(
                row["icd10_code"]
            )

            stats["parsed_rows"] += 1

            yield row

            if limit is not None and stats["parsed_rows"] == limit:
                break


# =========================================================
# DATABASE HELPERS
# =========================================================

def get_table_count(db, table_name):
    result = db.execute(
        text(
            "SELECT COUNT(*) FROM " + table_name
        )
    ).scalar()

    return int(result or 0)


def load_existing_icd10_codes(db):
    rows = db.execute(
        text(
            """
            SELECT icd10_code
            FROM icd10_master
            """
        )
    ).fetchall()

    return {
        normalize_icd10_code(row[0])
        for row in rows
        if row[0]
    }


def row_to_mapping(row):
    return {
        "icd10_code": row["icd10_code"],
        "diagnosis_description": row["diagnosis_description"],
        "display_name": row["display_name"],
        "chapter_code": row["chapter_code"],
        "chapter_name": row["chapter_name"],
        "billable": row["billable"],
        "active": row["active"],
        "effective_date": row["effective_date"],
        "retired_date": row["retired_date"],
        "search_text": row["search_text"],
    }


def upsert_batch(db, batch):
    if not batch:
        return

    table = ICD10Master.__table__

    statement = pg_insert(table).values(batch)

    update_values = {
        "diagnosis_description": statement.excluded.diagnosis_description,
        "display_name": statement.excluded.display_name,
        "chapter_code": statement.excluded.chapter_code,
        "chapter_name": statement.excluded.chapter_name,
        "billable": statement.excluded.billable,
        "active": statement.excluded.active,
        "effective_date": statement.excluded.effective_date,
        "retired_date": statement.excluded.retired_date,
        "search_text": statement.excluded.search_text,
        "updated_at": func.now(),
    }

    statement = statement.on_conflict_do_update(
        index_elements=["icd10_code"],
        set_=update_values,
    )

    db.execute(statement)


# =========================================================
# VALIDATION
# =========================================================

def validate_source_file(codes_file):
    if not codes_file.exists():
        raise FileNotFoundError(
            "ICD10 codes file not found: "
            + str(codes_file)
        )

    if not codes_file.is_file():
        raise FileNotFoundError(
            "ICD10 codes path is not a file: "
            + str(codes_file)
        )


def validate_post_import(db):
    total_count = get_table_count(
        db,
        "icd10_master",
    )

    active_count = db.execute(
        text(
            """
            SELECT COUNT(*)
            FROM icd10_master
            WHERE active = true
            """
        )
    ).scalar()

    billable_count = db.execute(
        text(
            """
            SELECT COUNT(*)
            FROM icd10_master
            WHERE billable = true
            """
        )
    ).scalar()

    blank_code_count = db.execute(
        text(
            """
            SELECT COUNT(*)
            FROM icd10_master
            WHERE icd10_code IS NULL
               OR length(trim(icd10_code)) = 0
            """
        )
    ).scalar()

    blank_description_count = db.execute(
        text(
            """
            SELECT COUNT(*)
            FROM icd10_master
            WHERE diagnosis_description IS NULL
               OR length(trim(diagnosis_description)) = 0
            """
        )
    ).scalar()

    print()
    print("POST-IMPORT VALIDATION")
    print("----------------------")
    print("Total ICD10 Master Rows      =", total_count)
    print("Active ICD10 Master Rows     =", int(active_count or 0))
    print("Billable ICD10 Master Rows   =", int(billable_count or 0))
    print("Blank ICD10 Codes            =", int(blank_code_count or 0))
    print("Blank Diagnosis Descriptions =", int(blank_description_count or 0))

    if int(blank_code_count or 0) != 0:
        raise RuntimeError(
            "Post-import validation failed: blank ICD10 codes found."
        )

    if int(blank_description_count or 0) != 0:
        raise RuntimeError(
            "Post-import validation failed: blank diagnosis descriptions found."
        )


# =========================================================
# IMPORT ENGINE
# =========================================================

def run_import(codes_file, batch_size, dry_run, limit):
    print()
    print("=" * 60)
    print("SNS HOSPICE EMR")
    print("ICD-10-CM FY2027 MASTER IMPORT")
    print("=" * 60)
    print()

    print("CONFIGURATION")
    print("-------------")
    print("Project Root =", PROJECT_ROOT)
    print("Codes File   =", codes_file)
    print("Batch Size   =", batch_size)
    print("Dry Run      =", dry_run)
    print("Limit        =", limit)
    print()

    validate_source_file(codes_file)

    db = SessionLocal()

    stats = {
        "source_lines": 0,
        "parsed_rows": 0,
        "skipped_blank_lines": 0,
        "skipped_duplicate_source_codes": 0,
        "parse_errors": 0,
        "estimated_inserts": 0,
        "estimated_updates": 0,
        "processed_batches": 0,
    }

    try:
        before_master_count = get_table_count(
            db,
            "icd10_master",
        )

        before_policy_count = get_table_count(
            db,
            "icd10_hospice_policy",
        )

        existing_codes = load_existing_icd10_codes(db)

        print("BEFORE")
        print("------")
        print("icd10_master         =", before_master_count)
        print("icd10_hospice_policy =", before_policy_count)
        print("Existing ICD10 Codes =", len(existing_codes))
        print()

        batch = []

        for row in iter_source_rows(
            codes_file,
            stats,
            limit,
        ):
            if row["icd10_code"] in existing_codes:
                stats["estimated_updates"] += 1
            else:
                stats["estimated_inserts"] += 1
                existing_codes.add(row["icd10_code"])

            batch.append(
                row_to_mapping(row)
            )

            if len(batch) == batch_size:
                upsert_batch(
                    db,
                    batch,
                )

                if dry_run:
                    db.rollback()
                else:
                    db.commit()

                stats["processed_batches"] += 1

                print(
                    "Progress: parsed="
                    + str(stats["parsed_rows"])
                    + ", estimated_inserts="
                    + str(stats["estimated_inserts"])
                    + ", estimated_updates="
                    + str(stats["estimated_updates"])
                    + ", batches="
                    + str(stats["processed_batches"])
                )

                batch = []

        if batch:
            upsert_batch(
                db,
                batch,
            )

            if dry_run:
                db.rollback()
            else:
                db.commit()

            stats["processed_batches"] += 1

        after_master_count = get_table_count(
            db,
            "icd10_master",
        )

        after_policy_count = get_table_count(
            db,
            "icd10_hospice_policy",
        )

        print()
        print("IMPORT SUMMARY")
        print("--------------")
        print("Source Lines Read              =", stats["source_lines"])
        print("Parsed ICD10 Rows              =", stats["parsed_rows"])
        print("Skipped Blank Lines            =", stats["skipped_blank_lines"])
        print("Skipped Duplicate Source Codes =", stats["skipped_duplicate_source_codes"])
        print("Parse Errors                   =", stats["parse_errors"])
        print("Estimated Inserts              =", stats["estimated_inserts"])
        print("Estimated Updates              =", stats["estimated_updates"])
        print("Batches Processed              =", stats["processed_batches"])
        print()

        print("AFTER")
        print("-----")
        print("icd10_master         =", after_master_count)
        print("icd10_hospice_policy =", after_policy_count)
        print()

        if dry_run:
            print("DRY RUN COMPLETE - no database changes were committed.")
            print()
            return

        validate_post_import(db)

        print()
        print("ICD-10-CM master import completed successfully.")
        print()

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


# =========================================================
# CLI
# =========================================================

def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Import CDC/NCHS ICD-10-CM FY2027 codes file into "
            "SNS Hospice EMR icd10_master."
        )
    )

    parser.add_argument(
        "--codes-file",
        type=Path,
        default=DEFAULT_CODES_FILE,
        help="Path to icd10cm-codes-2027.txt.",
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help="Number of rows per database batch.",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and execute import logic but rollback all database changes.",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional row limit for testing.",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    run_import(
        codes_file=args.codes_file,
        batch_size=args.batch_size,
        dry_run=args.dry_run,
        limit=args.limit,
    )


if __name__ == "__main__":
    main()
