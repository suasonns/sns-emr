from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.services.survey_token import decode_survey_token
from app.services.chart_pdf import generate_chart_summary_pdf
from app.core.db_session import SessionLocal
from app.api.patients import patient_chart_summary
from app.services.audit_logger import log_event

router = APIRouter(prefix="/survey", tags=["survey"])

@router.get(
    "/chart-summary/{token}",
    summary="Survey-mode chart PDF download",
)
def survey_chart_pdf(token: str):
    try:
        payload = decode_survey_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired survey token")

    if payload.get("type") != "survey" or payload.get("scope") != "chart_pdf":
        raise HTTPException(status_code=403, detail="Invalid token scope")

    patient_id = payload.get("patient_id")
    if not patient_id:
        raise HTTPException(status_code=400, detail="Missing patient reference")

    db: Session = SessionLocal()

    chart = patient_chart_summary(
        patient_id=patient_id,
        db=db,
        user=None,  # trusted due to token validation
    )

    pdf_buffer = generate_chart_summary_pdf(chart)

    log_event(
        user_id="SURVEY_TOKEN",
        role="Surveyor",
        action="SURVEY_PDF_ACCESS",
        entity_type="patient",
        entity_id=patient_id,
    )

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=chart-summary-{chart['patient']['mrn']}.pdf",
            "Cache-Control": "no-store",
            "Pragma": "no-cache",
        },
    )

