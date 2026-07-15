"""
SNS Hospice EMR
Documentation Integrity Runtime Verification

CURRENT PHASE:
RN ICA Compliance Completion -> Documentation Integrity Verification

PURPOSE:
Read-only runtime verification for:

1. Documentation Integrity Runtime Verification
2. Audit Traceability Walkthrough
3. Orphan Record Validation

STRICT RULES:
- VERIFY-FIRST
- READ-ONLY
- NO schema changes
- NO migrations
- NO alembic stamp
- NO unsafe automations
- NO data creation
- NO random tenants
- NO random patients

This script only inspects the current database state.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Any, Iterable

from sqlalchemy import inspect, text


# ============================================================
# DATABASE SESSION DISCOVERY
# ============================================================

def get_session_local():
    """
    Locate the project's SQLAlchemy SessionLocal without changing app code.
    """

    import_attempts = [
        "app.database",
        "app.db.database",
        "app.db.session",
        "app.core.database",
        "app.core.db",
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
        "Checked: app.database, app.db.database, app.db.session, "
        "app.core.database, app.core.db. "
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
# DB HELPERS
# ============================================================

def normalize_table_map(table_names: Iterable[str]) -> dict[str, str]:
    """
    Maps lower-case table names to actual table names.
    """
    return {name.lower(): name for name in table_names}


def table_exists(table_map: dict[str, str], table_name: str) -> bool:
    return table_name.lower() in table_map


def actual_table(table_map: dict[str, str], table_name: str) -> str | None:
    return table_map.get(table_name.lower())


def get_columns(inspector: Any, table_name: str) -> set[str]:
    return {column["name"] for column in inspector.get_columns(table_name)}


def first_existing_column(columns: set[str], candidates: list[str]) -> str | None:
    for candidate in candidates:
        if candidate in columns:
            return candidate
    return None


def existing_columns(columns: set[str], candidates: list[str]) -> list[str]:
    return [candidate for candidate in candidates if candidate in columns]


def safe_count(session: Any, sql: str, params: dict[str, Any] | None = None) -> int:
    result = session.execute(text(sql), params or {})
    value = result.scalar()
    return int(value or 0)


def safe_scalar(session: Any, sql: str, params: dict[str, Any] | None = None) -> Any:
    result = session.execute(text(sql), params or {})
    return result.scalar()


def q(identifier: str) -> str:
    """
    Quote a trusted identifier discovered from SQLAlchemy inspection.
    """
    return '"' + identifier.replace('"', '""') + '"'


# ============================================================
# TABLE DISCOVERY
# ============================================================

def discover_tables(table_map: dict[str, str]) -> dict[str, str | None]:
    candidates = {
        "patients": ["patients", "patient"],
        "users": ["users", "user", "staff", "employees"],
        "visits": ["visits", "visit"],
        "clinical_notes": ["clinical_notes", "clinical_note", "visit_notes", "notes"],
        "document_records": ["document_records", "documents", "clinical_documents"],
        "assessments": ["assessments", "assessment"],
        "admissions": ["admissions", "admission_records", "admission"],
        "tasks": ["tasks", "task"],
        "audit_logs": ["audit_logs", "audit_log", "audit_events"],
    }

    discovered: dict[str, str | None] = {}

    for logical_name, names in candidates.items():
        discovered[logical_name] = None
        for name in names:
            actual = actual_table(table_map, name)
            if actual is not None:
                discovered[logical_name] = actual
                break

    return discovered


# ============================================================
# DOCUMENTATION INTEGRITY VERIFICATION
# ============================================================

def verify_documentation_table(
    session: Any,
    inspector: Any,
    table_name: str,
    patients_table: str | None,
    users_table: str | None,
) -> None:
    category = "Documentation Integrity Runtime Verification"
    columns = get_columns(inspector, table_name)

    total = safe_count(session, f"SELECT COUNT(*) FROM {q(table_name)}")
    record(
        category,
        f"{table_name}: records exist",
        "PASS" if total > 0 else "WARN",
        f"{total} record(s) found.",
    )

    if "patient_id" in columns:
        missing_patient = safe_count(
            session,
            f"""
            SELECT COUNT(*)
            FROM {q(table_name)}
            WHERE patient_id IS NULL
            """
        )
        record(
            category,
            f"{table_name}: patient linkage present",
            "PASS" if missing_patient == 0 else "FAIL",
            f"{missing_patient} record(s) have NULL patient_id.",
        )

        if patients_table is not None:
            patient_columns = get_columns(inspector, patients_table)
            if "id" in patient_columns:
                orphan_patient = safe_count(
                    session,
                    f"""
                    SELECT COUNT(*)
                    FROM {q(table_name)} d
                    LEFT JOIN {q(patients_table)} p
                        ON d.patient_id = p.id
                    WHERE d.patient_id IS NOT NULL
                      AND p.id IS NULL
                    """
                )
                record(
                    category,
                    f"{table_name}: patient foreign-key reality check",
                    "PASS" if orphan_patient == 0 else "FAIL",
                    f"{orphan_patient} record(s) reference missing patients.",
                )
            else:
                record(
                    category,
                    f"{table_name}: patient foreign-key reality check",
                    "WARN",
                    f"{patients_table} table does not expose expected id column.",
                )
        else:
            record(
                category,
                f"{table_name}: patient foreign-key reality check",
                "WARN",
                "Patients table was not discovered.",
            )
    else:
        record(
            category,
            f"{table_name}: patient linkage present",
            "FAIL",
            "patient_id column not found.",
        )

    timestamp_candidates = [
        "created_at",
        "updated_at",
        "occurred_at",
        "completed_at",
        "signed_at",
        "finalized_at",
        "note_date",
        "visit_date",
    ]
    timestamp_columns = existing_columns(columns, timestamp_candidates)

    if timestamp_columns:
        null_condition = " AND ".join(
            f"{column} IS NULL" for column in timestamp_columns
        )
        missing_timestamp = safe_count(
            session,
            f"""
            SELECT COUNT(*)
            FROM {q(table_name)}
            WHERE {null_condition}
            """
        )
        record(
            category,
            f"{table_name}: timestamp traceability",
            "PASS" if missing_timestamp == 0 else "FAIL",
            f"{missing_timestamp} record(s) have no usable timestamp across {timestamp_columns}.",
        )
    else:
        record(
            category,
            f"{table_name}: timestamp traceability",
            "FAIL",
            "No recognized timestamp column found.",
        )

    author_candidates = [
        "author_id",
        "created_by",
        "created_by_id",
        "user_id",
        "clinician_id",
        "signed_by",
        "finalized_by",
    ]
    author_column = first_existing_column(columns, author_candidates)

    if author_column:
        missing_author = safe_count(
            session,
            f"""
            SELECT COUNT(*)
            FROM {q(table_name)}
            WHERE {author_column} IS NULL
            """
        )
        record(
            category,
            f"{table_name}: author linkage present",
            "PASS" if missing_author == 0 else "FAIL",
            f"{missing_author} record(s) have NULL {author_column}.",
        )

        if users_table is not None:
            user_columns = get_columns(inspector, users_table)
            if "id" in user_columns:
                orphan_author = safe_count(
                    session,
                    f"""
                    SELECT COUNT(*)
                    FROM {q(table_name)} d
                    LEFT JOIN {q(users_table)} u
                        ON d.{author_column} = u.id
                    WHERE d.{author_column} IS NOT NULL
                      AND u.id IS NULL
                    """
                )
                record(
                    category,
                    f"{table_name}: author foreign-key reality check",
                    "PASS" if orphan_author == 0 else "FAIL",
                    f"{orphan_author} record(s) reference missing users/staff.",
                )
            else:
                record(
                    category,
                    f"{table_name}: author foreign-key reality check",
                    "WARN",
                    f"{users_table} table does not expose expected id column.",
                )
        else:
            record(
                category,
                f"{table_name}: author foreign-key reality check",
                "WARN",
                "Users/staff table was not discovered.",
            )
    else:
        record(
            category,
            f"{table_name}: author linkage present",
            "FAIL",
            "No recognized author column found.",
        )

    discipline_candidates = [
        "discipline",
        "author_discipline",
        "clinician_discipline",
        "visit_discipline",
    ]
    discipline_column = first_existing_column(columns, discipline_candidates)

    if discipline_column:
        missing_discipline = safe_count(
            session,
            f"""
            SELECT COUNT(*)
            FROM {q(table_name)}
            WHERE {discipline_column} IS NULL
               OR TRIM(CAST({discipline_column} AS TEXT)) = ''
            """
        )
        record(
            category,
            f"{table_name}: discipline traceability",
            "PASS" if missing_discipline == 0 else "FAIL",
            f"{missing_discipline} record(s) have missing discipline in {discipline_column}.",
        )
    else:
        record(
            category,
            f"{table_name}: discipline traceability",
            "WARN",
            "No recognized discipline column found.",
        )

    if "visit_id" in columns:
        missing_visit_link = safe_count(
            session,
            f"""
            SELECT COUNT(*)
            FROM {q(table_name)}
            WHERE visit_id IS NULL
            """
        )
        record(
            category,
            f"{table_name}: visit-to-document linkage",
            "PASS" if missing_visit_link == 0 else "WARN",
            f"{missing_visit_link} record(s) have NULL visit_id. "
            "This may be valid for non-visit documents, but must be reviewed.",
        )
    else:
        record(
            category,
            f"{table_name}: visit-to-document linkage",
            "WARN",
            "visit_id column not found.",
        )

    if "tenant_id" in columns:
        missing_tenant = safe_count(
            session,
            f"""
            SELECT COUNT(*)
            FROM {q(table_name)}
            WHERE tenant_id IS NULL
            """
        )
        record(
            category,
            f"{table_name}: tenant attribution",
            "PASS" if missing_tenant == 0 else "FAIL",
            f"{missing_tenant} record(s) have NULL tenant_id.",
        )
    else:
        record(
            category,
            f"{table_name}: tenant attribution",
            "WARN",
            "tenant_id column not found on this table.",
        )


def verify_finalized_visits_have_documentation(
    session: Any,
    inspector: Any,
    visits_table: str | None,
    documentation_tables: list[str],
) -> None:
    category = "Documentation Integrity Runtime Verification"

    if visits_table is None:
        record(
            category,
            "Finalized visits have documentation",
            "FAIL",
            "Visits table was not discovered.",
        )
        return

    visit_columns = get_columns(inspector, visits_table)

    if "id" not in visit_columns:
        record(
            category,
            "Finalized visits have documentation",
            "FAIL",
            f"{visits_table} table does not expose expected id column.",
        )
        return

    status_column = first_existing_column(
        visit_columns,
        ["status", "visit_status", "state"],
    )

    if status_column is None:
        record(
            category,
            "Finalized visits have documentation",
            "FAIL",
            "No recognized visit status column found.",
        )
        return

    exists_clauses: list[str] = []

    for doc_table in documentation_tables:
        doc_columns = get_columns(inspector, doc_table)
        if "visit_id" in doc_columns:
            exists_clauses.append(
                f"""
                EXISTS (
                    SELECT 1
                    FROM {q(doc_table)} d
                    WHERE d.visit_id = v.id
                )
                """
            )

    if not exists_clauses:
        record(
            category,
            "Finalized visits have documentation",
            "FAIL",
            "No documentation tables with visit_id were discovered.",
        )
        return

    documentation_exists_sql = " OR ".join(exists_clauses)

    finalized_without_docs = safe_count(
        session,
        f"""
        SELECT COUNT(*)
        FROM {q(visits_table)} v
        WHERE UPPER(CAST(v.{status_column} AS TEXT)) IN (
            'FINALIZED',
            'COMPLETED',
            'SIGNED',
            'CLOSED'
        )
        AND NOT ({documentation_exists_sql})
        """
    )

    record(
        category,
        "Finalized visits have documentation",
        "PASS" if finalized_without_docs == 0 else "FAIL",
        f"{finalized_without_docs} finalized/completed/signed/closed visit(s) have no linked documentation.",
    )


def verify_admission_documentation(
    session: Any,
    inspector: Any,
    admissions_table: str | None,
    documentation_tables: list[str],
) -> None:
    category = "Documentation Integrity Runtime Verification"

    if admissions_table is None:
        record(
            category,
            "Admission documentation verification",
            "WARN",
            "Admissions table was not discovered.",
        )
        return

    admission_columns = get_columns(inspector, admissions_table)

    if "id" not in admission_columns:
        record(
            category,
            "Admission documentation verification",
            "WARN",
            f"{admissions_table} table does not expose expected id column.",
        )
        return

    total_admissions = safe_count(
        session,
        f"""
        SELECT COUNT(*)
        FROM {q(admissions_table)}
        """
    )

    if total_admissions == 0:
        record(
            category,
            "Admission documentation verification",
            "WARN",
            "No admission records found.",
        )
        return

    exists_clauses: list[str] = []

    for doc_table in documentation_tables:
        doc_columns = get_columns(inspector, doc_table)

        if "admission_id" in doc_columns:
            exists_clauses.append(
                f"""
                EXISTS (
                    SELECT 1
                    FROM {q(doc_table)} d
                    WHERE d.admission_id = a.id
                )
                """
            )

        if "source_id" in doc_columns and "source_type" in doc_columns:
            exists_clauses.append(
                f"""
                EXISTS (
                    SELECT 1
                    FROM {q(doc_table)} d
                    WHERE d.source_id = a.id
                      AND UPPER(CAST(d.source_type AS TEXT)) IN (
                          'ADMISSION',
                          'HOSPICE_ADMISSION',
                          'RN_ADMISSION'
                      )
                )
                """
            )

    if not exists_clauses:
        record(
            category,
            "Admission documentation verification",
            "WARN",
            "No admission_id/source admission linkage columns were discovered in documentation tables.",
        )
        return

    admission_doc_exists_sql = " OR ".join(exists_clauses)

    admissions_without_docs = safe_count(
        session,
        f"""
        SELECT COUNT(*)
        FROM {q(admissions_table)} a
        WHERE NOT ({admission_doc_exists_sql})
        """
    )

    record(
        category,
        "Admission documentation verification",
        "PASS" if admissions_without_docs == 0 else "FAIL",
        f"{admissions_without_docs} admission record(s) have no linked documentation.",
    )


# ============================================================
# ORPHAN RECORD VALIDATION
# ============================================================

def verify_orphan_records(
    session: Any,
    inspector: Any,
    patients_table: str | None,
    users_table: str | None,
    candidate_tables: list[str],
) -> None:
    category = "Orphan Record Validation"

    if patients_table is None:
        record(
            category,
            "Patient orphan validation",
            "FAIL",
            "Patients table was not discovered.",
        )
        return

    patient_columns = get_columns(inspector, patients_table)
    if "id" not in patient_columns:
        record(
            category,
            "Patient orphan validation",
            "FAIL",
            f"{patients_table} table does not expose expected id column.",
        )
        return

    for table_name in candidate_tables:
        columns = get_columns(inspector, table_name)

        if "patient_id" in columns:
            orphan_patient_count = safe_count(
                session,
                f"""
                SELECT COUNT(*)
                FROM {q(table_name)} r
                LEFT JOIN {q(patients_table)} p
                    ON r.patient_id = p.id
                WHERE r.patient_id IS NOT NULL
                  AND p.id IS NULL
                """
            )

            record(
                category,
                f"{table_name}: orphan patient references",
                "PASS" if orphan_patient_count == 0 else "FAIL",
                f"{orphan_patient_count} record(s) reference missing patients.",
            )

        author_column = first_existing_column(
            columns,
            [
                "author_id",
                "created_by",
                "created_by_id",
                "user_id",
                "clinician_id",
                "signed_by",
                "finalized_by",
                "updated_by",
            ],
        )

        if author_column and users_table is not None:
            user_columns = get_columns(inspector, users_table)

            if "id" in user_columns:
                orphan_author_count = safe_count(
                    session,
                    f"""
                    SELECT COUNT(*)
                    FROM {q(table_name)} r
                    LEFT JOIN {q(users_table)} u
                        ON r.{author_column} = u.id
                    WHERE r.{author_column} IS NOT NULL
                      AND u.id IS NULL
                    """
                )

                record(
                    category,
                    f"{table_name}: orphan author/user references",
                    "PASS" if orphan_author_count == 0 else "FAIL",
                    f"{orphan_author_count} record(s) reference missing users/staff via {author_column}.",
                )


# ============================================================
# AUDIT TRACEABILITY WALKTHROUGH
# ============================================================

def verify_audit_traceability(
    session: Any,
    inspector: Any,
    audit_logs_table: str | None,
) -> None:
    category = "Audit Traceability Walkthrough"

    if audit_logs_table is None:
        record(
            category,
            "Audit log table exists",
            "FAIL",
            "Audit log table was not discovered.",
        )
        return

    columns = get_columns(inspector, audit_logs_table)

    total_logs = safe_count(
        session,
        f"""
        SELECT COUNT(*)
        FROM {q(audit_logs_table)}
        """
    )

    record(
        category,
        "Audit logs exist",
        "PASS" if total_logs > 0 else "FAIL",
        f"{total_logs} audit log record(s) found.",
    )

    actor_column = first_existing_column(
        columns,
        [
            "actor_id",
            "user_id",
            "performed_by",
            "created_by",
            "changed_by",
        ],
    )

    timestamp_column = first_existing_column(
        columns,
        [
            "created_at",
            "timestamp",
            "event_time",
            "occurred_at",
        ],
    )

    action_column = first_existing_column(
        columns,
        [
            "action",
            "event_type",
            "operation",
            "activity",
        ],
    )

    entity_type_column = first_existing_column(
        columns,
        [
            "entity_type",
            "table_name",
            "resource_type",
            "record_type",
        ],
    )

    entity_id_column = first_existing_column(
        columns,
        [
            "entity_id",
            "record_id",
            "resource_id",
            "target_id",
        ],
    )

    required_mapping = {
        "actor": actor_column,
        "timestamp": timestamp_column,
        "action": action_column,
        "entity type/table": entity_type_column,
        "entity id/record id": entity_id_column,
    }

    for label, column in required_mapping.items():
        record(
            category,
            f"Audit log contains {label}",
            "PASS" if column else "FAIL",
            f"Column detected: {column}" if column else "No recognized column detected.",
        )

    if actor_column:
        missing_actor = safe_count(
            session,
            f"""
            SELECT COUNT(*)
            FROM {q(audit_logs_table)}
            WHERE {actor_column} IS NULL
            """
        )
        record(
            category,
            "Audit actor traceability",
            "PASS" if missing_actor == 0 else "FAIL",
            f"{missing_actor} audit log record(s) have NULL {actor_column}.",
        )

    if timestamp_column:
        missing_timestamp = safe_count(
            session,
            f"""
            SELECT COUNT(*)
            FROM {q(audit_logs_table)}
            WHERE {timestamp_column} IS NULL
            """
        )
        record(
            category,
            "Audit timestamp traceability",
            "PASS" if missing_timestamp == 0 else "FAIL",
            f"{missing_timestamp} audit log record(s) have NULL {timestamp_column}.",
        )

    if action_column:
        missing_action = safe_count(
            session,
            f"""
            SELECT COUNT(*)
            FROM {q(audit_logs_table)}
            WHERE {action_column} IS NULL
               OR TRIM(CAST({action_column} AS TEXT)) = ''
            """
        )
        record(
            category,
            "Audit action traceability",
            "PASS" if missing_action == 0 else "FAIL",
            f"{missing_action} audit log record(s) have missing action values.",
        )

    if entity_type_column:
        clinical_trace_count = safe_count(
            session,
            f"""
            SELECT COUNT(*)
            FROM {q(audit_logs_table)}
            WHERE UPPER(CAST({entity_type_column} AS TEXT)) IN (
                'CLINICAL_NOTES',
                'CLINICAL_NOTE',
                'VISITS',
                'VISIT',
                'DOCUMENT_RECORDS',
                'DOCUMENT',
                'ASSESSMENTS',
                'ASSESSMENT',
                'ADMISSIONS',
                'ADMISSION'
            )
            """
        )

        record(
            category,
            "Audit logs include clinical/documentation activity",
            "PASS" if clinical_trace_count > 0 else "WARN",
            f"{clinical_trace_count} clinical/documentation-related audit log record(s) found.",
        )


# ============================================================
# REPORTING
# ============================================================

def print_report() -> int:
    print()
    print("============================================================")
    print("SNS Hospice EMR")
    print("Documentation Integrity Runtime Verification")
    print("============================================================")
    print()

    grouped: dict[str, list[VerificationResult]] = {}

    for result in results:
        grouped.setdefault(result.category, []).append(result)

    fail_count = 0
    warn_count = 0
    pass_count = 0

    for category, category_results in grouped.items():
        print("------------------------------------------------------------")
        print(category)
        print("------------------------------------------------------------")

        for result in category_results:
            if result.status == "FAIL":
                fail_count += 1
            elif result.status == "WARN":
                warn_count += 1
            elif result.status == "PASS":
                pass_count += 1

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
        print("Documentation Integrity Runtime Verification can be considered verified if WARN items are clinically reviewed.")
        return 0

    print("FINAL RESULT: FAIL")
    print("Documentation Integrity Runtime Verification is NOT complete until FAIL items are corrected and re-verified.")
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

        table_names = inspector.get_table_names()
        table_map = normalize_table_map(table_names)
        discovered = discover_tables(table_map)

        patients_table = discovered["patients"]
        users_table = discovered["users"]
        visits_table = discovered["visits"]
        audit_logs_table = discovered["audit_logs"]
        admissions_table = discovered["admissions"]

        documentation_tables = [
            table
            for table in [
                discovered["clinical_notes"],
                discovered["document_records"],
                discovered["assessments"],
            ]
            if table is not None
        ]

        candidate_orphan_tables = [
            table
            for table in [
                discovered["visits"],
                discovered["clinical_notes"],
                discovered["document_records"],
                discovered["assessments"],
                discovered["admissions"],
                discovered["tasks"],
            ]
            if table is not None
        ]

        record(
            "Database Discovery",
            "Patients table discovery",
            "PASS" if patients_table else "FAIL",
            patients_table or "Not discovered.",
        )

        record(
            "Database Discovery",
            "Users/staff table discovery",
            "PASS" if users_table else "WARN",
            users_table or "Not discovered.",
        )

        record(
            "Database Discovery",
            "Visits table discovery",
            "PASS" if visits_table else "FAIL",
            visits_table or "Not discovered.",
        )

        record(
            "Database Discovery",
            "Documentation table discovery",
            "PASS" if documentation_tables else "FAIL",
            f"Discovered documentation tables: {documentation_tables}",
        )

        record(
            "Database Discovery",
            "Audit log table discovery",
            "PASS" if audit_logs_table else "FAIL",
            audit_logs_table or "Not discovered.",
        )

        for documentation_table in documentation_tables:
            verify_documentation_table(
                session=session,
                inspector=inspector,
                table_name=documentation_table,
                patients_table=patients_table,
                users_table=users_table,
            )

        verify_finalized_visits_have_documentation(
            session=session,
            inspector=inspector,
            visits_table=visits_table,
            documentation_tables=documentation_tables,
        )

        verify_admission_documentation(
            session=session,
            inspector=inspector,
            admissions_table=admissions_table,
            documentation_tables=documentation_tables,
        )

        verify_orphan_records(
            session=session,
            inspector=inspector,
            patients_table=patients_table,
            users_table=users_table,
            candidate_tables=candidate_orphan_tables,
        )

        verify_audit_traceability(
            session=session,
            inspector=inspector,
            audit_logs_table=audit_logs_table,
        )

        return print_report()

    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())