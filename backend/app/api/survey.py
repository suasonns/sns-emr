from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.bulk_reauth_guard import require_bulk_print_reauth
from app.core.bulk_rules import is_bulk_action
from app.core.database import get_db
from app.dependencies.auth import get_current_user

from app.services.chart_pdf import generate_chart_summary_pdf
from app.api.patients import patient_chart_summary
from app.services.audit_logger import log_event
from app.services.survey_export import build_survey_export_zip
from app.services.security_activity_logger import log_security_activity

router = APIRouter(prefix="/survey", tags=["Survey Mode"])


# ------------------------------------------------------------
# Survey Mode SQL (read-only, regulator-safe)
# ------------------------------------------------------------
SURVEY_OVERDUE_POC_SQL = text("SELECT * FROM survey_overdue_poc_updates")
SURVEY_IDG_COMPLIANCE_SQL = text("SELECT * FROM survey_idg_compliance")
SURVEY_CRISIS_POC_SQL = text("SELECT * FROM survey_crisis_poc_same_day")


# ------------------------------------------------------------
# Chart Summary PDF
# Permission: download_chart_pdf
# ------------------------------------------------------------
@router.get("/chart-summary", summary="Survey-mode chart PDF download")
def survey_chart_pdf(
    patient_id: str = Query(..., description="Patient UUID"),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not has_permission(current_user, "download_chart_pdf"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    chart = patient_chart_summary(
        patient_id=patient_id,
        db=db,
        user=current_user,
    )

    pdf_buffer = generate_chart_summary_pdf(chart)

    user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
    role = current_user.get("role") if isinstance(current_user, dict) else current_user.role

    log_event(
        user_id=user_id,
        role=role,
        action="SURVEY_PDF_ACCESS",
        entity_type="patient",
        entity_id=patient_id,
    )

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=chart-summary-{patient_id}.pdf",
            "Cache-Control": "no-store",
            "Pragma": "no-cache",
        },
    )


# ------------------------------------------------------------
# Compliance Views
# Permission: view_compliance
# ------------------------------------------------------------
@router.get("/overdue-poc-updates")
def overdue_poc_updates(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not has_permission(current_user, "view_compliance"):
        raise HTTPException(status_code=403)

    result = db.execute(SURVEY_OVERDUE_POC_SQL)
    return [dict(row) for row in result.mappings()]


@router.get("/idg-compliance")
def idg_compliance(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not has_permission(current_user, "view_compliance"):
        raise HTTPException(status_code=403)

    result = db.execute(SURVEY_IDG_COMPLIANCE_SQL)
    return [dict(row) for row in result.mappings()]


@router.get("/crisis-poc-same-day")
def crisis_poc_same_day(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not has_permission(current_user, "view_compliance"):
        raise HTTPException(status_code=403)

    result = db.execute(SURVEY_CRISIS_POC_SQL)
    return [dict(row) for row in result.mappings()]


# ------------------------------------------------------------
# Export Bundle (BULK) — requires step‑up auth token
# Permission: export_data
# ------------------------------------------------------------
@router.get("/export-bundle", summary="One-click survey export bundle (ZIP)")
def survey_export_bundle(
    reauth_token: str | None = Query(
        None,
        description="Step-up authentication token required for bulk export",
    ),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not has_permission(current_user, "export_data"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    user_id = current_user.get("id") if isinstance(current_user, dict) else current_user.id
    role = current_user.get("role") if isinstance(current_user, dict) else current_user.role

    # Log ATTEMPT
    log_security_activity(
        db=db,
        user_id=user_id,
        role=role,
        event_type="BULK_EXPORT_ATTEMPT",
        scope="SURVEY_EXPORT_BUNDLE",
        patient_count=2,
        document_count=0,
        result="INFO",
    )

    # Enforce step-up auth
    if is_bulk_action(document_count=0, patient_count=2):
        require_bulk_print_reauth(
            reauth_token=reauth_token,
            user_id=user_id,
            db=db,
        )

    # Log ALLOWED
    log_security_activity(
        db=db,
        user_id=user_id,
        role=role,
        event_type="BULK_EXPORT_ALLOWED",
        scope="SURVEY_EXPORT_BUNDLE",
        patient_count=2,
        document_count=0,
        result="ALLOWED",
    )

    zip_buffer = build_survey_export_zip(db)

    log_event(
        user_id=user_id,
        role=role,
        action="SURVEY_EXPORT_BUNDLE",
        entity_type="system",
        entity_id="survey_export",
    )

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": "attachment; filename=survey-export.zip",
            "Cache-Control": "no-store",
            "Pragma": "no-cache",
        },
    )