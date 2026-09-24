"""ADR/TPE export endpoint (Compliance Mode).

LOCKED:
- Runs full audit first.
- Binary readiness.
- READY => cover sheet + ADR packet PDF
- NOT READY => deficiency report PDF only
- Does not affect Manual Print Chart.

"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Response, HTTPException

from app.core.capabilities import VIEW_ALL_TENANT_PATIENTS, require_capability
from app.core.patient_access import get_authorized_patient
from app.core.security import CurrentUser
from app.db.session import get_db
from app.schemas.adr_audit import AdrExportRequest
from app.services.adr_audit_service import AdrAuditService
from app.services.adr_pdf_utils import render_deficiency_report, render_adr_cover_sheet
from app.services.audit_logger import log_event

router = APIRouter(prefix="/chart", tags=["chart"])


@router.post("/export/adr", response_class=Response)
def export_adr(
    req: AdrExportRequest,
    db=Depends(get_db),
    # AC-003 remediation: authentication + tenant-wide-oversight
    # authorization, reusing the same capability already required for
    # Survey Mode compliance/export actions (app.core.capabilities).
    user: CurrentUser = Depends(require_capability(VIEW_ALL_TENANT_PATIENTS)),
):
    if not req.adr_mode:
        raise HTTPException(status_code=400, detail="adr_mode must be true for ADR export")

    try:
        patient_uuid = uuid.UUID(str(req.patient_id))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Patient not found") from exc

    # AC-003 remediation: bind the client-supplied patient_id to the
    # authenticated user's own tenant via the existing tenant-isolation +
    # care-team-scoping helper (app.core.patient_access) instead of
    # trusting the identifier as-is. Raises 404 if the patient does not
    # belong to this user's tenant or is otherwise not authorized.
    patient = get_authorized_patient(db, patient_uuid, user)

    # NOTE: run_full_audit()'s parameters are keyword-only; the pre-existing
    # call here passed them positionally, which meant this endpoint raised
    # a TypeError on every single invocation regardless of auth -- a
    # separate, pre-existing defect discovered while validating AC-003,
    # fixed here only because it otherwise prevents "preserve export
    # behavior for authorized users" from being verifiable at all.
    audit_service = AdrAuditService(db)
    audit = audit_service.run_full_audit(
        patient_id=str(patient.id), adr_start=req.adr_start, adr_end=req.adr_end, mode=req.mode
    )

    # AC-003 remediation: audit the export itself using the existing
    # audit infrastructure (app.services.audit_logger), matching the
    # pattern already used for Survey Mode chart access.
    log_event(
        user_id=str(user.user_id),
        tenant_id=str(user.tenant_id),
        role=user.role,
        action="ADR_EXPORT",
        entity_type="patient",
        entity_id=str(patient.id),
        db=db,
    )

    if not audit.ready:
        pdf_bytes = render_deficiency_report(audit)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=ADR_DEFICIENCY_REPORT.pdf"},
        )

    cover = render_adr_cover_sheet(audit)
    return Response(
        content=cover,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=ADR_PACKET.pdf"},
    )
