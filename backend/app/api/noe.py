from datetime import datetime, timezone, date
import json
import logging
import base64

from fastapi import APIRouter, Body, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.services.noe_pdf import fill_noe_pdf
from app.models.benefit_period import BenefitPeriod
from app.billing.services.noe_penalty_service import compute_noe_penalty

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/patients", tags=["NOE"])


# ---------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------

class NOEOverrides(BaseModel):
    agency_name: str | None = None
    patient_full_name: str | None = None
    mbi: str | None = None
    gender: str | None = None
    address: str | None = None

    is_transferee: bool | None = None
    is_in_snf: bool | None = None
    snf_name: str | None = None
    snf_address_1: str | None = None
    snf_address_2: str | None = None


class NOEPdfResponse(BaseModel):
    file_name: str
    content_type: str
    pdf_base64: str


class NOESubmissionUpdate(BaseModel):
    noe_submitted_date: date | None = None
    noe_exception_reason: str | None = None


class NOEPenaltyResponse(BaseModel):
    election_date: str | None
    noe_submitted_date: str | None
    noe_exception_reason: str | None
    is_late: bool
    is_exempt: bool
    non_covered_start: str | None
    non_covered_end: str | None
    non_covered_days: int
    reason: str | None


# ---------------------------------------------------------------------
# Audit helpers (SCHEMA‑SAFE)
# ---------------------------------------------------------------------

def _get_table_columns(db: Session, table_name: str) -> dict[str, str]:
    rows = db.execute(
        text("""
            SELECT column_name, udt_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = :t
        """),
        {"t": table_name},
    ).fetchall()
    return {r[0]: r[1] for r in rows}


def _current_benefit_period_id(db: Session, patient_id: str) -> str | None:
    row = db.execute(
        text("""
            SELECT id
            FROM benefit_periods
            WHERE patient_id = :pid
              AND start_date <= (now() at time zone 'utc')
              AND (end_date IS NULL OR end_date >= (now() at time zone 'utc'))
            ORDER BY start_date DESC
            LIMIT 1
        """),
        {"pid": patient_id},
    ).mappings().first()
    return row["id"] if row else None


def _log_noe_event(
    db: Session,
    patient_id: str,
    user_id: str | None,
    result: str,
    reasons: list[str] | None,
):
    cols = _get_table_columns(db, "noe_audit_events")
    now_utc = datetime.now(timezone.utc)
    reasons_list = reasons or []

    insert_cols: list[str] = []
    params: dict = {}

    if "patient_id" in cols:
        insert_cols.append("patient_id")
        params["patient_id"] = patient_id

    if "event_type" in cols:
        insert_cols.append("event_type")
        params["event_type"] = result

    if "event_at" in cols:
        insert_cols.append("event_at")
        params["event_at"] = now_utc

    if "performed_by_user_id" in cols:
        insert_cols.append("performed_by_user_id")
        params["performed_by_user_id"] = user_id

    if "benefit_period_id" in cols:
        insert_cols.append("benefit_period_id")
        params["benefit_period_id"] = _current_benefit_period_id(db, patient_id)

    if "reasons" in cols:
        insert_cols.append("reasons")
        if cols["reasons"] == "jsonb":
            params["reasons"] = json.dumps(reasons_list)
        else:
            params["reasons"] = reasons_list

    if not insert_cols:
        raise RuntimeError("no compatible columns in noe_audit_events")

    values_sql = []
    for c in insert_cols:
        if c == "reasons" and cols.get("reasons") == "jsonb":
            values_sql.append(f":{c}::jsonb")
        else:
            values_sql.append(f":{c}")

    sql = f"""
        INSERT INTO noe_audit_events ({", ".join(insert_cols)})
        VALUES ({", ".join(values_sql)})
    """

    db.execute(text(sql), params)
    db.commit()


def safe_log_noe_event(
    db: Session,
    patient_id: str,
    user_id: str | None,
    result: str,
    reasons: list[str] | None,
):
    try:
        _log_noe_event(db, patient_id, user_id, result, reasons)
    except Exception:
        logger.exception(
            "NOE audit logging failed",
            extra={"patient_id": patient_id, "user_id": user_id},
        )


# ---------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------

@router.post(
    "/{patient_id}/noe/generate-pdf",
    status_code=status.HTTP_200_OK,
    response_model=NOEPdfResponse,
    summary="Generate NOE PDF (base64)",
    operation_id="GenerateNoePdf",
)
def generate_noe_pdf(
    patient_id: str,
    overrides: NOEOverrides = Body(default_factory=NOEOverrides),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Generate a pre-filled NOE PDF for manual faxing.
    DOES NOT submit to Medicare.
    """

    user_id = current_user.get("id") if isinstance(current_user, dict) else None

    tenant_id = (
        current_user.get("tenant_id")
        if isinstance(current_user, dict)
        else getattr(current_user, "tenant_id", None)
    )

    if not tenant_id:
        raise HTTPException(status_code=401, detail="Missing tenant")

    readiness = db.execute(
        text("""
            SELECT patient_status, allergy_state
            FROM patient_face_sheet_view
            WHERE patient_id = :pid
              AND tenant_id = :tenant_id
        """),
        {"pid": patient_id, "tenant_id": str(tenant_id)},
    ).mappings().first()

    if not readiness:
        raise HTTPException(status_code=404, detail="Patient not found")

    reasons: list[str] = []

    if readiness["patient_status"] != "ACTIVE":
        reasons.append("Patient is not admitted (status is not ACTIVE)")

    if readiness["allergy_state"] in (None, "NOT_DOCUMENTED", "UNKNOWN"):
        reasons.append("Allergy status not documented")

    rn_dx = db.execute(
        text("""
            SELECT icd_code
            FROM diagnosis_sources
            WHERE patient_id = :pid
              AND tenant_id = :tenant_id
              AND source = 'RN_IA'
              AND dx_type = 'PRIMARY'
              AND is_active = true
            ORDER BY documented_at DESC
            LIMIT 1
        """),
        {"pid": patient_id, "tenant_id": str(tenant_id)},
    ).mappings().first()

    if not rn_dx:
        reasons.append("RN Initial Assessment primary diagnosis is missing")

    if reasons:
        safe_log_noe_event(db, patient_id, user_id, "BLOCKED", reasons)
        raise HTTPException(
            status_code=409,
            detail={
                "message": "NOE PDF cannot be generated because patient is not NOE-ready.",
                "reasons": reasons,
            },
        )

    data = {
        "agency_name": overrides.agency_name or "",
        "patient_full_name": overrides.patient_full_name or "",
        "mbi": overrides.mbi or "",
        "gender": overrides.gender or "",
        "address": overrides.address or "",
        "primary_dx_code": rn_dx["icd_code"],
        "sent_by": user_id or "SYSTEM",
        "generated_at": datetime.now(timezone.utc),
    }

    try:
        pdf_bytes = fill_noe_pdf(data)
    except Exception as e:
        logger.exception("NOE PDF generation failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"NOE PDF generation failed: {type(e).__name__}",
        )

    safe_log_noe_event(db, patient_id, user_id, "GENERATED", [])

    return {
        "file_name": f"NOE_{patient_id}.pdf",
        "content_type": "application/pdf",
        "pdf_base64": base64.b64encode(pdf_bytes).decode("utf-8"),
    }


def _get_initial_benefit_period(db: Session, patient_id: str) -> BenefitPeriod:
    bp = db.execute(
        text(
            """
            SELECT id FROM benefit_periods
            WHERE patient_id::text = :pid AND period_number = 1
            ORDER BY start_date ASC
            LIMIT 1
            """
        ),
        {"pid": patient_id},
    ).mappings().first()

    if not bp:
        raise HTTPException(
            status_code=404,
            detail="No INITIAL (period_number=1) benefit period on file for this patient.",
        )

    row = db.get(BenefitPeriod, bp["id"])
    if row is None:
        raise HTTPException(status_code=404, detail="Benefit period not found")
    return row


@router.patch(
    "/{patient_id}/noe/submission",
    response_model=NOEPenaltyResponse,
    summary="Record the real NOE filing date (or a CMS exception) for the patient's initial election",
    operation_id="UpdateNoeSubmission",
)
def update_noe_submission(
    patient_id: str,
    payload: NOESubmissionUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Records the real date the NOE was filed with the MAC (or a documented
    CMS exception waiving the late-filing penalty) against the patient's
    INITIAL benefit period. This is the single source of truth the billing
    engine uses (noe_penalty_service.compute_noe_penalty) to determine
    whether any RHC/GIP/CHC/Respite days must be zeroed out as non-covered
    under 42 CFR 418.24(b). Never fabricate a submission date here -- only
    record what actually happened.
    """
    user_id = current_user.get("id") if isinstance(current_user, dict) else None

    bp = _get_initial_benefit_period(db, patient_id)

    bp.noe_submitted_date = payload.noe_submitted_date
    bp.noe_exception_reason = payload.noe_exception_reason
    db.add(bp)
    db.commit()
    db.refresh(bp)

    safe_log_noe_event(
        db,
        patient_id,
        user_id,
        "SUBMISSION_RECORDED",
        [f"noe_submitted_date={payload.noe_submitted_date}"] if payload.noe_submitted_date else [],
    )

    penalty = compute_noe_penalty(
        election_date=bp.election_date,
        noe_submitted_date=bp.noe_submitted_date,
        exception_reason=bp.noe_exception_reason,
    )

    return {
        "election_date": bp.election_date.isoformat() if bp.election_date else None,
        "noe_submitted_date": bp.noe_submitted_date.isoformat() if bp.noe_submitted_date else None,
        "noe_exception_reason": bp.noe_exception_reason,
        "is_late": penalty.is_late,
        "is_exempt": penalty.is_exempt,
        "non_covered_start": penalty.non_covered_start.isoformat() if penalty.non_covered_start else None,
        "non_covered_end": penalty.non_covered_end.isoformat() if penalty.non_covered_end else None,
        "non_covered_days": penalty.non_covered_days,
        "reason": penalty.reason,
    }


@router.get(
    "/{patient_id}/noe/submission",
    response_model=NOEPenaltyResponse,
    summary="Preview the current NOE filing status and any late-filing penalty",
    operation_id="GetNoeSubmission",
)
def get_noe_submission(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    bp = _get_initial_benefit_period(db, patient_id)

    penalty = compute_noe_penalty(
        election_date=bp.election_date,
        noe_submitted_date=bp.noe_submitted_date,
        exception_reason=bp.noe_exception_reason,
    )

    return {
        "election_date": bp.election_date.isoformat() if bp.election_date else None,
        "noe_submitted_date": bp.noe_submitted_date.isoformat() if bp.noe_submitted_date else None,
        "noe_exception_reason": bp.noe_exception_reason,
        "is_late": penalty.is_late,
        "is_exempt": penalty.is_exempt,
        "non_covered_start": penalty.non_covered_start.isoformat() if penalty.non_covered_start else None,
        "non_covered_end": penalty.non_covered_end.isoformat() if penalty.non_covered_end else None,
        "non_covered_days": penalty.non_covered_days,
        "reason": penalty.reason,
    }