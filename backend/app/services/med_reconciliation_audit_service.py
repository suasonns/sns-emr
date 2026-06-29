from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.med_reconciliation_audit_log import MedReconciliationAuditLog


HASH_VERSION = "sha256-v1"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _resolve_created_by_from_session(db: Session):
    raw = db.info.get("user_id")
    if not raw:
        return None

    try:
        return raw if isinstance(raw, uuid.UUID) else uuid.UUID(str(raw))
    except Exception:
        return None


def _uuid_to_lock_key(value) -> int:
    """
    Convert UUID to a stable positive bigint for PostgreSQL advisory locks.
    Uses the lower 63 bits to stay safely within signed bigint range.
    """
    as_uuid = value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))
    return as_uuid.int & 0x7FFFFFFFFFFFFFFF


def _canonical_json(value: Any) -> str:
    """
    Deterministic JSON serialization for hashing.
    """
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    )


def _compute_signature_hash(
    *,
    tenant_id,
    patient_id,
    import_id,
    item_id,
    stage: str,
    event_type: str,
    med_name_raw: Optional[str],
    input_payload: Optional[dict[str, Any]],
    normalized_payload: Optional[dict[str, Any]],
    comparison_payload: Optional[dict[str, Any]],
    decision_payload: Optional[dict[str, Any]],
    created_by,
    created_at: datetime,
    prev_signature_hash: Optional[str],
) -> str:
    """
    Compute SHA-256 over immutable audit fields + previous chain hash.
    """
    material = {
        "hash_version": HASH_VERSION,
        "tenant_id": str(tenant_id) if tenant_id else None,
        "patient_id": str(patient_id) if patient_id else None,
        "import_id": str(import_id) if import_id else None,
        "item_id": str(item_id) if item_id else None,
        "stage": stage,
        "event_type": event_type,
        "med_name_raw": med_name_raw,
        "input_payload": input_payload,
        "normalized_payload": normalized_payload,
        "comparison_payload": comparison_payload,
        "decision_payload": decision_payload,
        "created_by": str(created_by) if created_by else None,
        "created_at": created_at.isoformat(),
        "prev_signature_hash": prev_signature_hash,
    }

    canonical = _canonical_json(material).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _latest_hash_for_patient(db: Session, patient_id) -> Optional[str]:
    """
    Get the latest audit hash in the patient-specific chain.
    Caller is expected to hold the advisory transaction lock first.
    """
    row = (
        db.query(MedReconciliationAuditLog.signature_hash)
        .filter(MedReconciliationAuditLog.patient_id == patient_id)
        .order_by(MedReconciliationAuditLog.created_at.desc(), MedReconciliationAuditLog.id.desc())
        .first()
    )
    return row[0] if row else None


def log_med_reconciliation_audit_event(
    *,
    db: Session,
    tenant_id,
    patient_id,
    import_id=None,
    item_id=None,
    stage: str,
    event_type: str,
    med_name_raw: Optional[str] = None,
    input_payload: Optional[dict[str, Any]] = None,
    normalized_payload: Optional[dict[str, Any]] = None,
    comparison_payload: Optional[dict[str, Any]] = None,
    decision_payload: Optional[dict[str, Any]] = None,
):
    """
    Insert one immutable med reconciliation audit log row with SHA-256 hash chaining.

    Security properties:
    - per-row SHA-256 hash over immutable audit fields
    - patient-scoped prev_signature_hash chain
    - advisory transaction lock to reduce concurrent chain forks

    Caller owns the transaction (no commit here).
    """
    created_by = _resolve_created_by_from_session(db)
    created_at = _utcnow()

    # ---------------------------------------------------------
    # Acquire patient-scoped advisory lock so concurrent inserts
    # for the same patient do not fork the hash chain.
    # ---------------------------------------------------------
    lock_key = _uuid_to_lock_key(patient_id)
    db.execute(
        text("SELECT pg_advisory_xact_lock(:key)"),
        {"key": lock_key},
    )

    prev_signature_hash = _latest_hash_for_patient(db, patient_id)

    signature_hash = _compute_signature_hash(
        tenant_id=tenant_id,
        patient_id=patient_id,
        import_id=import_id,
        item_id=item_id,
        stage=stage,
        event_type=event_type,
        med_name_raw=med_name_raw,
        input_payload=input_payload,
        normalized_payload=normalized_payload,
        comparison_payload=comparison_payload,
        decision_payload=decision_payload,
        created_by=created_by,
        created_at=created_at,
        prev_signature_hash=prev_signature_hash,
    )

    record = MedReconciliationAuditLog(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        patient_id=patient_id,
        import_id=import_id,
        item_id=item_id,
        stage=stage,
        event_type=event_type,
        med_name_raw=med_name_raw,
        input_payload=input_payload,
        normalized_payload=normalized_payload,
        comparison_payload=comparison_payload,
        decision_payload=decision_payload,
        created_by=created_by,
        created_at=created_at,
        hash_version=HASH_VERSION,
        prev_signature_hash=prev_signature_hash,
        signature_hash=signature_hash,
    )

    db.add(record)
    db.flush()

    return record