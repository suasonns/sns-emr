from __future__ import annotations

import argparse
import logging
import sys
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Sequence

from sqlalchemy import bindparam, text

from app.db.session import SessionLocal

logger = logging.getLogger("med_recon_backfill_sql")


# =========================================================
# CONSTANTS
# =========================================================

UNRESOLVED_REVIEW_STATUSES = {"PENDING"}
ACTIVE_TASK_STATUSES_PREFERRED = ["PENDING", "IN_PROGRESS", "OVERDUE"]
CLOSING_TASK_STATUS_PREFERRED = ["EXCUSED", "CANCELLED", "COMPLETED"]
COMPLETION_REFERENCE_TYPE_PREFERRED = "DOCUMENT"
DUPLICATE_SUPERSEDED_NOTE_PREFIX = "[AUTO-SUPERSEDED DUPLICATE]"


# =========================================================
# LOGGING
# =========================================================

def _configure_logging(verbose: bool) -> None:
    level = logging.INFO if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


# =========================================================
# HELPERS
# =========================================================

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _parse_uuid_or_none(value: Optional[str]) -> Optional[uuid.UUID]:
    if not value:
        return None
    return uuid.UUID(str(value))


def _scalar_list(rows: Sequence[tuple]) -> List[str]:
    result: List[str] = []
    for row in rows:
        if not row:
            continue
        result.append(str(row[0]))
    return result


def _get_table_columns(db, table_name: str) -> Dict[str, Dict[str, str]]:
    rows = db.execute(
        text(
            """
            SELECT
                column_name,
                data_type,
                udt_name,
                is_nullable
            FROM information_schema.columns
            WHERE table_name = :table_name
            ORDER BY ordinal_position
            """
        ),
        {"table_name": table_name},
    ).fetchall()

    result: Dict[str, Dict[str, str]] = {}
    for row in rows:
        result[str(row.column_name)] = {
            "data_type": str(row.data_type),
            "udt_name": str(row.udt_name),
            "is_nullable": str(row.is_nullable),
        }
    return result


def _get_enum_labels(db, type_name: str) -> List[str]:
    rows = db.execute(
        text(
            """
            SELECT e.enumlabel
            FROM pg_type t
            JOIN pg_enum e ON e.enumtypid = t.oid
            WHERE t.typname = :type_name
            ORDER BY e.enumsortorder
            """
        ),
        {"type_name": type_name},
    ).fetchall()
    return [str(row[0]) for row in rows]


def _pick_closing_task_status(db, tasks_columns: Dict[str, Dict[str, str]]) -> str:
    status_column = tasks_columns.get("status")
    if not status_column:
        raise RuntimeError("tasks.status column not found")

    udt_name = status_column["udt_name"]
    labels = _get_enum_labels(db, udt_name)

    for candidate in CLOSING_TASK_STATUS_PREFERRED:
        if candidate in labels:
            return candidate

    raise RuntimeError(
        f"No suitable closing task status found in enum {udt_name}; labels={labels}"
    )


def _completion_reference_document_allowed(
    db,
    tasks_columns: Dict[str, Dict[str, str]],
) -> bool:
    column = tasks_columns.get("completion_reference_type")
    if not column:
        return False

    udt_name = column["udt_name"]
    if not udt_name or udt_name in {"varchar", "text"}:
        return True

    labels = _get_enum_labels(db, udt_name)
    return COMPLETION_REFERENCE_TYPE_PREFERRED in labels


def _build_signature_exprs(item_columns: Dict[str, Dict[str, str]]) -> List[str]:
    """
    Build normalized grouping expressions for duplicate detection.
    Always includes med_name_normalized.
    Add normalized dose/route/frequency fields only if present.
    """
    exprs = [
        "lower(trim(med_name_normalized)) AS med_name_key",
    ]

    optional_candidates = [
        "dose_normalized",
        "route_normalized",
        "frequency_normalized",
    ]

    for col in optional_candidates:
        if col in item_columns:
            exprs.append(f"lower(trim(coalesce({col}, ''))) AS {col}_key")

    return exprs


def _build_signature_select_columns(item_columns: Dict[str, Dict[str, str]]) -> List[str]:
    cols = [
        "patient_id",
        "med_name_key",
    ]

    if "dose_normalized" in item_columns:
        cols.append("dose_normalized_key")

    if "route_normalized" in item_columns:
        cols.append("route_normalized_key")

    if "frequency_normalized" in item_columns:
        cols.append("frequency_normalized_key")

    return cols


def _append_note_sql(existing_column_name: str = "notes") -> str:
    return (
        f"COALESCE({existing_column_name}, '') || "
        "CASE WHEN COALESCE({col}, '') = '' THEN :note ELSE E'\\n' || :note END"
    ).format(col=existing_column_name)


# =========================================================
# CORE BACKFILL
# =========================================================

def collapse_duplicate_backlog_sql(
    *,
    db,
    patient_id: Optional[uuid.UUID] = None,
) -> dict:
    item_columns = _get_table_columns(db, "med_reconciliation_items")
    task_columns = _get_table_columns(db, "tasks")

    if "med_name_normalized" not in item_columns:
        raise RuntimeError(
            "med_reconciliation_items.med_name_normalized is required for duplicate collapse"
        )

    if "review_status" not in item_columns:
        raise RuntimeError(
            "med_reconciliation_items.review_status column not found"
        )

    if "reference_id" not in task_columns or "reference_type" not in task_columns:
        raise RuntimeError(
            "tasks.reference_id/reference_type columns are required for duplicate task cleanup"
        )

    now = _utcnow()

    signature_exprs = _build_signature_exprs(item_columns)
    signature_select_columns = _build_signature_select_columns(item_columns)

    patient_filter_sql = ""
    patient_params = {}
    if patient_id is not None:
        patient_filter_sql = "AND patient_id = :patient_id"
        patient_params["patient_id"] = patient_id

    grouped_sql = f"""
        WITH unresolved AS (
            SELECT
                id,
                patient_id,
                created_at,
                {", ".join(signature_exprs)}
            FROM med_reconciliation_items
            WHERE review_status = 'PENDING'
              AND med_name_normalized IS NOT NULL
              {patient_filter_sql}
        )
        SELECT
            {", ".join(signature_select_columns)},
            COUNT(*) AS item_count
        FROM unresolved
        GROUP BY {", ".join(signature_select_columns)}
        HAVING COUNT(*) > 1
        ORDER BY patient_id, med_name_key
    """

    grouped_rows = db.execute(text(grouped_sql), patient_params).fetchall()

    signatures_examined = 0
    survivor_item_ids: List[str] = []
    superseded_item_ids: List[str] = []
    closed_task_ids: List[str] = []

    active_task_labels = _pick_existing_task_statuses(
        db=db,
        tasks_columns=task_columns,
        preferred=ACTIVE_TASK_STATUSES_PREFERRED,
    )
    closing_status = _pick_closing_task_status(db, task_columns)
    can_write_completion_reference_type = _completion_reference_document_allowed(
        db,
        task_columns,
    )

    for row in grouped_rows:
        signatures_examined += 1

        med_name_key = str(row.med_name_key)
        patient_uuid = row.patient_id

        filters = [
            "patient_id = :patient_id",
            "review_status = 'PENDING'",
            "med_name_normalized IS NOT NULL",
            "lower(trim(med_name_normalized)) = :med_name_key",
        ]
        params = {
            "patient_id": patient_uuid,
            "med_name_key": med_name_key,
        }

        if "dose_normalized" in item_columns:
            filters.append("lower(trim(coalesce(dose_normalized, ''))) = :dose_key")
            params["dose_key"] = str(getattr(row, "dose_normalized_key"))
        if "route_normalized" in item_columns:
            filters.append("lower(trim(coalesce(route_normalized, ''))) = :route_key")
            params["route_key"] = str(getattr(row, "route_normalized_key"))
        if "frequency_normalized" in item_columns:
            filters.append("lower(trim(coalesce(frequency_normalized, ''))) = :frequency_key")
            params["frequency_key"] = str(getattr(row, "frequency_normalized_key"))

        duplicate_items_sql = f"""
            SELECT
                id,
                import_id,
                patient_id,
                med_name_raw,
                med_name_normalized,
                created_at
            FROM med_reconciliation_items
            WHERE {" AND ".join(filters)}
            ORDER BY created_at DESC, id DESC
        """

        duplicate_items = db.execute(text(duplicate_items_sql), params).fetchall()
        if len(duplicate_items) <= 1:
            # Should not happen because HAVING COUNT(*) > 1, but keep safe
            continue

        survivor = duplicate_items[0]
        older_duplicates = duplicate_items[1:]
        older_duplicate_ids = [row.id for row in older_duplicates]

        survivor_item_ids.append(str(survivor.id))

        logger.info(
            "MED_RECON_BACKFILL_SQL: survivor_item_id=%s duplicate_count=%s med_name_key=%s patient_id=%s",
            str(survivor.id),
            len(duplicate_items),
            med_name_key,
            str(patient_uuid),
        )

        # -----------------------------------------------------
        # STEP 1 — SUPERSEDE OLDER DUPLICATE ITEMS
        # -----------------------------------------------------
        if older_duplicate_ids:
            note = (
                f"{DUPLICATE_SUPERSEDED_NOTE_PREFIX} "
                f"Superseded by newer unresolved duplicate item {survivor.id} "
                f"for normalized medication '{med_name_key}'."
            )

            set_clauses = [
                "review_status = 'REJECTED'",
                "updated_at = :now",
            ]
            update_params = {
                "now": now,
                "ids": older_duplicate_ids,
            }

            if "notes" in item_columns:
                set_clauses.append(f"notes = {_append_note_sql('notes')}")
                update_params["note"] = note

            update_items_sql = text(
                f"""
                UPDATE med_reconciliation_items
                SET {", ".join(set_clauses)}
                WHERE id IN :ids
                """
            ).bindparams(bindparam("ids", expanding=True))

            db.execute(update_items_sql, update_params)

            superseded_item_ids.extend([str(x) for x in older_duplicate_ids])

        # -----------------------------------------------------
        # STEP 2 — CLOSE OLDER ACTIVE TASKS LINKED TO THOSE ITEMS
        # -----------------------------------------------------
        if older_duplicate_ids:
            task_query_sql = text(
                """
                SELECT id
                FROM tasks
                WHERE reference_type = 'MED_RECON_ITEM'
                  AND reference_id IN :ids
                  AND status IN :statuses
                ORDER BY created_at ASC
                """
            ).bindparams(
                bindparam("ids", expanding=True),
                bindparam("statuses", expanding=True),
            )

            task_rows = db.execute(
                task_query_sql,
                {
                    "ids": older_duplicate_ids,
                    "statuses": active_task_labels,
                },
            ).fetchall()

            task_ids = [row.id for row in task_rows]

            if task_ids:
                task_set_clauses = [
                    "status = :closing_status",
                    "updated_at = :now",
                ]
                task_update_params = {
                    "closing_status": closing_status,
                    "now": now,
                    "task_ids": task_ids,
                }

                if "completed_at" in task_columns:
                    task_set_clauses.append("completed_at = :now")

                if "excused_reason_code" in task_columns:
                    task_set_clauses.append("excused_reason_code = :excused_reason_code")
                    task_update_params["excused_reason_code"] = "DUPLICATE_SUPERSEDED"

                if "excused_source" in task_columns:
                    task_set_clauses.append("excused_source = :excused_source")
                    task_update_params["excused_source"] = "BACKFILL_DEDUP"

                if "excused_at" in task_columns:
                    task_set_clauses.append("excused_at = :now")

                if "completion_reference_id" in task_columns:
                    task_set_clauses.append("completion_reference_id = :survivor_item_id")
                    task_update_params["survivor_item_id"] = survivor.id

                if (
                    "completion_reference_type" in task_columns
                    and can_write_completion_reference_type
                ):
                    task_set_clauses.append(
                        "completion_reference_type = :completion_reference_type"
                    )
                    task_update_params["completion_reference_type"] = COMPLETION_REFERENCE_TYPE_PREFERRED

                if "escalation_reason" in task_columns:
                    task_set_clauses.append("escalation_reason = :escalation_reason")
                    task_update_params["escalation_reason"] = (
                        f"Historical duplicate reconciliation task superseded by active item {survivor.id}"
                    )

                if "is_overdue" in task_columns:
                    task_set_clauses.append("is_overdue = false")

                update_tasks_sql = text(
                    f"""
                    UPDATE tasks
                    SET {", ".join(task_set_clauses)}
                    WHERE id IN :task_ids
                    """
                ).bindparams(bindparam("task_ids", expanding=True))

                db.execute(update_tasks_sql, task_update_params)

                closed_task_ids.extend([str(x) for x in task_ids])

    return {
        "signatures_examined": signatures_examined,
        "survivor_item_ids": survivor_item_ids,
        "superseded_item_ids": superseded_item_ids,
        "closed_task_ids": closed_task_ids,
    }


def _pick_existing_task_statuses(
    *,
    db,
    tasks_columns: Dict[str, Dict[str, str]],
    preferred: List[str],
) -> List[str]:
    status_column = tasks_columns.get("status")
    if not status_column:
        raise RuntimeError("tasks.status column not found")

    labels = _get_enum_labels(db, status_column["udt_name"])
    return [status for status in preferred if status in labels]


# =========================================================
# CLI
# =========================================================

def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "One-time SQL backfill to collapse historical duplicate med reconciliation backlog. "
            "Default is DRY RUN. Use --commit to persist changes."
        )
    )
    parser.add_argument(
        "--patient-id",
        default=None,
        help="Optional patient UUID to scope cleanup to one patient",
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Persist changes. Without this flag, the script rolls back.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable INFO-level logging",
    )

    args = parser.parse_args()
    _configure_logging(args.verbose)

    try:
        patient_uuid = _parse_uuid_or_none(args.patient_id)
    except Exception as exc:
        print(f"Invalid --patient-id: {exc}", file=sys.stderr)
        return 2

    db = SessionLocal()

    try:
        result = collapse_duplicate_backlog_sql(
            db=db,
            patient_id=patient_uuid,
        )

        if args.commit:
            db.commit()
            action = "COMMITTED"
        else:
            db.rollback()
            action = "DRY_RUN_ROLLED_BACK"

        print(
            {
                "action": action,
                "patient_id": str(patient_uuid) if patient_uuid else None,
                **result,
            }
        )
        return 0

    except Exception as exc:
        db.rollback()
        print(f"Backfill failed: {exc}", file=sys.stderr)
        return 1

    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
