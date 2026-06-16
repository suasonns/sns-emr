from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Dict, List, Optional
import uuid

AUDIT_EVENTS: List[Dict] = []


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_audit_event(
    *,
    event_type: str,
    patient_id: str,
    billing_cycle_id: str,
    actor: str,
    previous_status: Optional[str] = None,
    new_status: Optional[str] = None,
    reason: Optional[str] = None,
    claim_control_number: Optional[str] = None,
    details: Optional[Dict] = None,
) -> Dict:
    return {
        "audit_id": str(uuid.uuid4()),
        "timestamp": utc_now_iso(),
        "event_type": event_type,
        "patient_id": patient_id,
        "billing_cycle_id": billing_cycle_id,
        "actor": actor,
        "previous_status": previous_status,
        "new_status": new_status,
        "reason": reason,
        "claim_control_number": claim_control_number,
        "details": details or {},
    }


def append_audit_event(event: Dict) -> Dict:
    AUDIT_EVENTS.append(event)
    return deepcopy(event)


def list_audit_events(
    patient_id: Optional[str] = None,
    billing_cycle_id: Optional[str] = None,
) -> List[Dict]:
    results = AUDIT_EVENTS

    if patient_id:
        results = [e for e in results if e.get("patient_id") == patient_id]

    if billing_cycle_id:
        results = [e for e in results if e.get("billing_cycle_id") == billing_cycle_id]

    return deepcopy(sorted(results, key=lambda x: x.get("timestamp", ""), reverse=True))