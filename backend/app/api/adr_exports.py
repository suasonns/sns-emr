"""ADR/TPE export endpoint (Compliance Mode).

LOCKED:
- Runs full audit first.
- Binary readiness.
- READY => cover sheet + ADR packet PDF
- NOT READY => deficiency report PDF only
- Does not affect Manual Print Chart.

"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response, HTTPException

from app.db.session import get_db
from app.schemas.adr_audit import AdrExportRequest
from app.services.adr_audit_service import AdrAuditService
from app.services.adr_pdf_utils import render_deficiency_report, render_adr_cover_sheet

router = APIRouter(prefix="/chart", tags=["chart"])


@router.post("/export/adr", response_class=Response)
def export_adr(req: AdrExportRequest, db=Depends(get_db)):
    if not req.adr_mode:
        raise HTTPException(status_code=400, detail="adr_mode must be true for ADR export")

    audit_service = AdrAuditService(db)
    audit = audit_service.run_full_audit(req.patient_id, req.adr_start, req.adr_end, mode=req.mode)

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
