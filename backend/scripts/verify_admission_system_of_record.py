"""
SNS Hospice EMR
Admission System of Record Verification

CURRENT PHASE:
RN ICA Compliance Completion -> Documentation Integrity Verification

OPEN DEFECT:
DEFECT-004 - Admission System of Record Not Verified

PURPOSE:
Read-only verification to determine whether SNS EMR has a clear
admission system of record.

STRICT RULES:
- VERIFY-FIRST
- READ-ONLY
- NO schema changes
- NO migrations
- NO alembic stamp
- NO data creation
- NO random tenants
- NO random patients
- NO repair until classified

This script does not decide architecture.
It only identifies current database reality.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Any

from sqlalchemy import inspect, text


# ============================================================
# SESSION DISCOVERY
# ============================================================

def get_session_local():
    import_attempts = [
        "app.core.database",
        "app.db.session",
        "app.core.db",
        "app.db.database",
    ]

    last_error = None

    for module_name in import_attempts:
        try:
            module = __import__(module_name, fromlist=["SessionLocal"])
            session_local = getattr(module, "SessionLocal", None)
            if session_local is not None:
                return session_local
        except Exception as exc:
            last_error = exc

    raise RuntimeError(
        "Unable to locate SessionLocal. "
        "Checked app.core.database, app.db.session, app.core.db, app.db.database. "
        f"Last error: {last_error}"
    )


# ============================================================
# RESULT MODEL
# ============================================================

@dataclass
class VerificationResult:
    category: str
    check_name: str
    status: str
    detail: str


results: list[VerificationResult] = []


def record(category: str, check_name: str, status: str, detail: str) -> None:
    results.append(
        VerificationResult(
            category=category,
            check_name=check_name,
            status=status,
            detail=detail,
        )
    )


# ============================================================
# HELPERS
# ============================================================

def q(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def safe_count(session: Any, table_name: str) -> int:
    value = session.execute(text(f"SELECT COUNT(*) FROM {q(table_name)}")).scalar()
    return int(value or 0)


def get_columns(inspector: Any, table_name: str) -> list[str]:
    return [column["name"] for column in inspector.get_columns(table_name)]


def find_columns(columns: list[str], keywords: list[str]) -> listmatches: list[str] = []

    for column in columns:
        lower_column = column.lower()
        for keyword in keywords:
            if keyword.lower() in lower_column:
                matches.append(column)
                break

    return matches


# ============================================================
# VERIFICATION LOGIC
# ============================================================

def verify_standalone_admission_table(table_names: list[str]) -> None:
    category = "Admission System of Record Verification"

    expected_names = [
        "admission",
        "admissions",
        "admission_records",
        "patient_admissions",
        "hospice_admissions",
    ]

    found = [name for name in expected_names if name in table_names]

    if found:
        record(
            category,
            "Standalone admission table discovery",
            "PASS",
            f"Standalone admission table(s) found: {found}",
        )
    else:
        record(
            category,
            "Standalone admission table discovery",
            "FAIL",
            "No standalone admission table found using expected names: "
            f"{expected_names}",
        )


def verify_admission_related_tables(
    session: Any,
    inspector: Any,
    table_names: list[str],
) -> None:
    category = "Admission-Related Table Review"

    relevant_table_candidates = [
        "patients",
        "patient",
        "patient_facesheet",
        "certifications",
        "benefit_periods",
        "authorization_records",
        "f2f_encounters",
        "tasks",
        "clinical_notes",
        "document_records",
        "assessments",
        "patient_diagnoses",
        "plan_of_care",
    ]

    discovered = [
        table_name
        for table_name in relevant_table_candidates
        if table_name in table_names
    ]

    record(
        category,
        "Admission-related table discovery",
        "PASS" if discovered else "FAIL",
        f"Discovered related tables: {discovered}",
    )

    admission_keywords = [
        "admission",
        "admit",
        "soc",
        "start_of_care",
        "election",
        "authorized",
        "authorization",
        "certification",
        "benefit",
        "noe",
        "cti",
    ]

    for table_name in discovered:
        columns = get_columns(inspector, table_name)
        count = safe_count(session, table_name)
        matched_columns = find_columns(columns, admission_keywords)

        if matched_columns:
            status = "PASS"
            detail = (
                f"{count} record(s). Admission-related columns found: "
                f"{matched_columns}"
            )
        else:
            status = "WARN"
            detail = (
                f"{count} record(s). No obvious admission-related columns found. "
                f"Available columns: {columns}"
            )

        record(
            category,
            f"{table_name}: admission-related column scan",
            status,
            detail,
        )


def verify_rn_ica_prerequisite_candidates(
    session: Any,
    inspector: Any,
    table_names: list[str],
) -> None:
    category = "RN ICA Admission Prerequisite Review"

    candidate_tables = [
        "tasks",
        "clinical_notes",
        "assessments",
        "forms",
        "form_registry",
        "form_modules",
        "clinical_workflow_map",
    ]

    discovered = [table for table in candidate_tables if table in table_names]

    record(
        category,
        "RN ICA workflow table discovery",
        "PASS" if discovered else "FAIL",
        f"Discovered RN ICA workflow candidate tables: {discovered}",
    )

    rn_ica_keywords = [
        "rn_ica",
        "initial_rn_ica",
        "ica",
        "assessment",
        "admission",
        "soc",
    ]

    for table_name in discovered:
        columns = get_columns(inspector, table_name)
        count = safe_count(session, table_name)
        matched_columns = find_columns(columns, rn_ica_keywords)

        record(
            category,
            f"{table_name}: RN ICA/admission linkage column scan",
            "PASS" if matched_columns else "WARN",
            (
                f"{count} record(s). Matched columns: {matched_columns}"
                if matched_columns
                else f"{count} record(s). No obvious RN ICA/admission linkage columns found."
            ),
        )


def verify_required_gateway_conclusion(table_names: list[str]) -> None:
    category = "Preliminary Classification"

    standalone_admission_exists = any(
        table_name in table_names
        for table_name in [
            "admission",
            "admissions",
            "admission_records",
            "patient_admissions",
            "hospice_admissions",
        ]
    )

    if standalone_admission_exists:
        record(
            category,
            "Preliminary admission architecture classification",
            "PASS",
            "A standalone admission table exists. Next step is to verify its "
            "relationships to patients, RN ICA, tasks, documents, and audit logs.",
        )
    else:
        record(
            category,
            "Preliminary admission architecture classification",
            "FAIL",
            "No standalone admission table exists. This must be classified as either "
            "intentional distributed architecture or missing admission aggregate. "
            "Do not close RN ICA Compliance Completion until classified.",
        )


# ============================================================
# REPORTING
# ============================================================

def print_report() -> int:
    print()
    print("============================================================")
    print("SNS Hospice EMR")
    print("Admission System of Record Verification")
    print("============================================================")
    print()

    grouped: dict[str, list[VerificationResult]] = {}

    for result in results:
        grouped.setdefault(result.category, []).append(result)

    pass_count = 0
    warn_count = 0
    fail_count = 0

    for category, category_results in grouped.items():
        print("------------------------------------------------------------")
        print(category)
        print("------------------------------------------------------------")

        for result in category_results:
            if result.status == "PASS":
                pass_count += 1
            elif result.status == "WARN":
                warn_count += 1
            elif result.status == "FAIL":
                fail_count += 1

            print(f"[{result.status}] {result.check_name}")
            print(f"       {result.detail}")

        print()

    print("============================================================")
    print("SUMMARY")
    print("============================================================")
    print(f"PASS: {pass_count}")
    print(f"WARN: {warn_count}")
    print(f"FAIL: {fail_count}")
    print()

    if fail_count == 0:
        print("FINAL RESULT: PASS")
        print("Admission System of Record Verification did not detect a blocking failure.")
        return 0

    print("FINAL RESULT: FAIL")
    print("Admission System of Record is NOT verified.")
    print("RN ICA Compliance Completion must remain ACTIVE until this is classified and repaired if needed.")
    return 1


# ============================================================
# MAIN
# ============================================================

def main() -> int:
    SessionLocal = get_session_local()
    session = SessionLocal()

    try:
        bind = session.get_bind()
        inspector = inspect(bind)
        table_names = sorted(inspector.get_table_names())

        verify_standalone_admission_table(table_names)
        verify_admission_related_tables(session, inspector, table_names)
        verify_rn_ica_prerequisite_candidates(session, inspector, table_names)
        verify_required_gateway_conclusion(table_names)

        return print_report()

    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())