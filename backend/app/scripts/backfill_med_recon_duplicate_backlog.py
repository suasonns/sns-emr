from __future__ import annotations

import argparse
import logging
import sys
import uuid
from typing import List
from collections import defaultdict
from datetime import datetime, timezone
from typing import Iterable, Optional

# ✅ FORCE LOAD ALL MODELS (CRITICAL FOR SQLALCHEMY MAPPERS)

import app.models.medication
import app.models.patient
import app.models.task
import app.models.med_reconciliation

# ✅ Load ALL model modules once to ensure mapper relationships resolve

import importlib

MODEL_MODULES = [
    "app.models.patient",
    "app.models.medication",
    "app.models.task",
    "app.models.med_reconciliation",
]

for module in MODEL_MODULES:
    importlib.import_module(module)

# ✅ FORCE MODEL REGISTRATION (FULL SAFE LOAD)

from app.db.base import Base  # ✅ if you have this file (most setups do)

# ✅ Import ALL model modules so SQLAlchemy relationships resolve
import app.models

# ✅ FORCE MODEL REGISTRATION WITHOUT BASE

import importlib

MODULES = [
    "app.models.patient",
    "app.models.medication",
    "app.models.task",
    "app.models.med_reconciliation",
]

for m in MODULES:
    importlib.import_module(m)

# ---------------------------------------------------------
# DB Session import fallback
# ---------------------------------------------------------
try:
    from app.db.session import SessionLocal
except Exception:
    try:
        from app.core.database import SessionLocal  # fallback used elsewhere in SNS EMR
    except Exception as exc:
        raise RuntimeError(
            "Unable to import SessionLocal from app.db.session or app.core.database"
        ) from exc

from app.models.med_reconciliation import MedReconciliationItem
from app.models.task import Task
from app.models.enums import TaskStatus

logger = logging.getLogger("med_recon_backfill")


UNRESOLVED_REVIEW_STATUSES = {"PENDING"}
DUPLICATE_SUPERSEDED_NOTE_PREFIX = "[AUTO-SUPERSEDED DUPLICATE]"
ALERT_PREFIX = "MED_RECON"


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


def _pick_task_status(*candidate_names: str):
    for name in candidate_names:
        if hasattr(TaskStatus, name):
            return getattr(TaskStatus, name)
    raise ValueError(f"TaskStatus does not contain any of: {candidate_names}")


def _set_if_present(obj, **values) -> None:
    """
    Set ORM attributes only if the SQLAlchemy model exposes them.
    """
    for key, value in values.items():
        if hasattr(obj, key):
            setattr(obj, key, value)


def _append_note(existing: Optional[str], addition: str) -> str:
    existing_value = (existing or "").strip()
    if not existing_value:
        return addition
    return f"{existing_value}\n{addition}"

def _signature_for_item(item: MedReconciliationItem) -> tuple:
    """
    Duplicate signature:
    - patient_id
    - med_name_normalized
    - optional normalized dose/route/frequency if ORM exposes them
    """
    med_name_normalized = getattr(item, "med_name_normalized", None)
    dose_normalized = getattr(item, "dose_normalized", None) if hasattr(item, "dose_normalized") else None
    route_normalized = getattr(item, "route_normalized", None) if hasattr(item, "route_normalized") else None
    frequency_normalized = getattr(item, "frequency_normalized", None) if hasattr(item, "frequency_normalized") else None

    return (
        str(item.patient_id),
        str(med_name_normalized).strip().lower() if med_name_normalized else None,
        str(dose_normalized).strip().lower() if dose_normalized else None,
        str(route_normalized).strip().lower() if route_normalized else None,
        str(frequency_normalized).strip().lower() if frequency_normalized else None,
    )



def _iter_candidate_items(db, patient_id: Optional[uuid.UUID]) -> List[MedReconciliationItem]:
    query = (
        db.query(MedReconciliationItem)
        .filter(MedReconciliationItem.review_status.in_(UNRESOLVED_REVIEW_STATUSES))
    )

    if patient_id is not None:
        query = query.filter(MedReconciliationItem.patient_id == patient_id)

    query = query.order_by(
        MedReconciliationItem.patient_id.asc(),
        MedReconciliationItem.created_at.desc(),
        MedReconciliationItem.id.desc(),
    )

    return query.all()

def _active_task_statuses():
    values = []
    for candidate in ("PENDING", "IN_PROGRESS", "OVERDUE"):
        if hasattr(TaskStatus, candidate):
            values.append(getattr(TaskStatus, candidate))
    return values


def _closing_task_status():
    for candidate in ("EXCUSED", "CANCELLED", "COMPLETED"):
        if hasattr(TaskStatus, candidate):
            return getattr(TaskStatus, candidate)
    raise ValueError("No suitable task closing status found in TaskStatus enum")


# =========================================================
# CORE BACKFILL LOGIC
# =========================================================

def collapse_duplicate_backlog(
    *,
    db,
    patient_id: Optional[uuid.UUID] = None,
) -> dict:
    """
    Collapse historical med reconciliation duplicate backlog.

    Rules:
    - only unresolved items (currently review_status=PENDING)
    - require med_name_normalized to be present
    - keep newest item as survivor
    - older duplicates become REJECTED
    - older active tasks for those item ids are closed
    """

    now = _utcnow()

    items = list(_iter_candidate_items(db, patient_id))
    grouped: dict[tuple, list[MedReconciliationItem]] = defaultdict(list)

    # ---------------------------------------------------------
    # GROUP UNRESOLVED ITEMS BY NORMALIZED SIGNATURE
    # ---------------------------------------------------------
    for item in items:
        signature = _signature_for_item(item)

        # skip rows that cannot safely participate in duplicate grouping
        # because there is no normalized med identity
        if signature[1] is None:
            continue

        grouped[signature].append(item)

    signatures_examined = 0
    survivor_item_ids: list[str] = []
    superseded_item_ids: list[str] = []
    closed_task_ids: list[str] = []

    active_statuses = _active_task_statuses()
    closing_status = _closing_task_status()

    # ---------------------------------------------------------
    # PROCESS EACH DUPLICATE GROUP
    # ---------------------------------------------------------
    for signature, group in grouped.items():
        if len(group) <= 1:
            continue

        signatures_examined += 1

        # items already ordered by created_at DESC overall, but sort explicitly
        group = sorted(
            group,
            key=lambda x: (
                getattr(x, "created_at", datetime.min.replace(tzinfo=timezone.utc)),
                str(getattr(x, "id", "")),
            ),
            reverse=True,
        )

        survivor = group[0]
        older_duplicates = group[1:]

        survivor_item_ids.append(str(survivor.id))

        med_name_normalized = signature[1]

        logger.info(
            "MED_RECON_BACKFILL: survivor=%s duplicates=%s med_name_normalized=%s patient_id=%s",
            str(survivor.id),
            len(group),
            med_name_normalized,
            str(survivor.patient_id),
        )

        # -----------------------------------------------------
        # STEP 1 — SUPERSEDE OLDER DUPLICATE ITEMS
        # -----------------------------------------------------
        for item in older_duplicates:
            item.review_status = "REJECTED"
            item.updated_at = now

            note = (
                f"{DUPLICATE_SUPERSEDED_NOTE_PREFIX} "
                f"Superseded by newer unresolved duplicate item {survivor.id} "
                f"for normalized medication '{med_name_normalized}'."
            )

            _set_if_present(
                item,
                notes=_append_note(getattr(item, "notes", None), note),
            )

            superseded_item_ids.append(str(item.id))

        older_duplicate_ids = [item.id for item in older_duplicates]

        # -----------------------------------------------------
        # STEP 2 — CLOSE OLDER ACTIVE TASKS LINKED TO THOSE ITEMS
        # -----------------------------------------------------
        tasks = (
            db.query(Task)
            .filter(Task.reference_type == "MED_RECON_ITEM")
            .filter(Task.reference_id.in_(older_duplicate_ids))
            .filter(Task.status.in_(active_statuses))
            .order_by(Task.created_at.asc())
            .all()
        )

        for task in tasks:
            task.status = closing_status
            task.updated_at = now

            _set_if_present(
                task,
                completed_at=now,
                completion_reference_type="DOCUMENT",
                completion_reference_id=survivor.id,
                excused_reason_code="DUPLICATE_SUPERSEDED",
                excused_source="BACKFILL_DEDUP",
                excused_at=now,
                escalation_reason=(
                    f"Historical duplicate reconciliation task superseded by active item {survivor.id}"
                ),
                is_overdue=False,
            )

            closed_task_ids.append(str(task.id))

    return {
        "signatures_examined": signatures_examined,
        "survivor_item_ids": survivor_item_ids,
        "superseded_item_ids": superseded_item_ids,
        "closed_task_ids": closed_task_ids,
    }


# =========================================================
# CLI ENTRYPOINT
# =========================================================

def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "One-time backfill to collapse historical duplicate med reconciliation backlog. "
            "Default mode is DRY RUN. Use --commit to persist changes."
        )
    )
    parser.add_argument(
        "--patient-id",
        help="Optional patient UUID to limit the cleanup to one patient",
        default=None,
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Persist changes. Without this flag, the script performs a dry run and rolls back.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable INFO-level logging",
    )

    args = parser.parse_args()

    _configure_logging(args.verbose)

    patient_uuid = None
    try:
        patient_uuid = _parse_uuid_or_none(args.patient_id)
    except Exception as exc:
        print(f"Invalid --patient-id: {exc}", file=sys.stderr)
        return 2

    db = SessionLocal()

    try:
        result = collapse_duplicate_backlog(
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