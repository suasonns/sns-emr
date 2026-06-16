"""ADR readiness banner endpoint (Guidance-only Layer 1).

This endpoint reuses the same full audit results to drive a persistent
"NOT READY FOR ADR" banner in the UI.

No blocking: signing is allowed; this endpoint provides visibility.
"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query

from app.db.session import get_db
from app.schemas.adr_audit import AdrReadinessBanner
from app.services.adr_audit_service import AdrAuditService

router = APIRouter(prefix="/patients", tags=["adr"])


@router.get("/{patient_id}/adr-readiness", response_model=AdrReadinessBanner)
def get_adr_readiness(
    patient_id: str,
    adr_start: date = Query(...),
    adr_end: date = Query(...),
    mode: str = Query("ADR"),
    db=Depends(get_db),
):
    audit = AdrAuditService(db).run_full_audit(patient_id, adr_start, adr_end, mode=mode)
    fail_count = len(audit.findings)

    if audit.ready:
        text = "READY FOR ADR"
        top = []
    else:
        top = [f.rule_id for f in audit.findings[:5]]
        text = f"NOT READY FOR ADR — {fail_count} issue(s) must be resolved before submission"

    return AdrReadinessBanner(
        ready=audit.ready,
        banner_text=text,
        fail_count=fail_count,
        top_fail_rules=top,
        audit=audit,
    )
