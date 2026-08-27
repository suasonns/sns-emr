from __future__ import annotations

from datetime import date, datetime, timedelta
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.roles import access_scope_for_role
from app.core.tenant_scope import (
    list_billable_agency_tenants,
    resolve_billing_scope_tenant_id,
)

from app.billing.security import require_automated_billing
from app.billing.engine.billing_engine import (
    BillingEngineError,
    generate_patient_billing,
)
from app.billing.services.claim_export_service import (
    ClaimExportError,
    build_patient_claim_export,
)
from app.billing.services.edi_builder import (
    EDIBuilderError,
    build_837i_text,
    save_edi_to_file,
)
from app.billing.services.billing_readiness_service import (
    check_patient_billing_readiness,
    build_tenant_billing_readiness_report,
)
from app.billing.schemas.billing_schema import (
    GetOrCreateBillingCycleRequest,
    BillingCycleResponse,
    GeneratePatientBillingRequest,
    GeneratePatientBillingResponse,
    BuildPatientClaimExportRequest,
    BuildPatientClaimExportResponse,
    BuildPatientClaimEDIRequest,
    BuildPatientClaimEDIResponse,
    PatientBillingReadinessResponse,
    TenantBillingReadinessReportResponse,
    BatchGeneratePatientBillingRequest,
    BatchGeneratePatientBillingResponse,
)
from app.billing.validators.claim_validator import validate_claim
from app.billing.models.claim_export_log import ClaimExportLog
from app.billing.models.claim import Claim
from app.billing.models.claim_edi_batch import ClaimEdiBatch
from app.billing.models.billing_cycle import BillingCycle


# =========================================================
# ROUTER
# =========================================================

router = APIRouter(prefix="/billing", tags=["Billing"])


# =========================================================
# BILLING CYCLE (GET-OR-CREATE) — REAL, TENANT-SCOPED
# =========================================================

@router.post(
    "/cycles",
    response_model=BillingCycleResponse,
)
def get_or_create_billing_cycle(
    payload: GetOrCreateBillingCycleRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Returns the tenant's billing cycle for the given month/year, creating it
    (OPEN, calendar-month bounds) if it doesn't exist yet. Idempotent —
    protected by the tenant+month+year unique constraint on billing_cycles.

    This is the real entry point that was missing: nothing else in the app
    created BillingCycle rows, so generate_patient_billing() had no way to
    ever run against real data.
    """
    require_automated_billing(db, str(user.tenant_id))

    tenant_id = str(user.tenant_id)

    existing = (
        db.query(BillingCycle)
        .filter(
            BillingCycle.tenant_id == tenant_id,
            BillingCycle.month == payload.month,
            BillingCycle.year == payload.year,
        )
        .one_or_none()
    )

    if existing is None:
        start_date = date(payload.year, payload.month, 1)
        end_date = date(
            payload.year + (1 if payload.month == 12 else 0),
            1 if payload.month == 12 else payload.month + 1,
            1,
        ) - timedelta(days=1)

        existing = BillingCycle(
            id=uuid4(),
            tenant_id=tenant_id,
            month=payload.month,
            year=payload.year,
            start_date=start_date,
            end_date=end_date,
            status="OPEN",
            created_by=str(getattr(user, "user_id", None) or ""),
        )
        db.add(existing)

        try:
            db.commit()
        except IntegrityError:
            # Concurrent request already created it — fetch the real row.
            db.rollback()
            existing = (
                db.query(BillingCycle)
                .filter(
                    BillingCycle.tenant_id == tenant_id,
                    BillingCycle.month == payload.month,
                    BillingCycle.year == payload.year,
                )
                .one()
            )
        else:
            db.refresh(existing)

    return {
        "id": str(existing.id),
        "tenant_id": str(existing.tenant_id),
        "month": existing.month,
        "year": existing.year,
        "start_date": str(existing.start_date),
        "end_date": str(existing.end_date),
        "status": existing.status,
        "created_at": existing.created_at.isoformat() if existing.created_at else "",
    }


# =========================================================
# BILLING GENERATION (AUTOMATED ONLY)
# =========================================================

@router.post(
    "/generate-patient",
    response_model=GeneratePatientBillingResponse,
)
def generate_patient(
    payload: GeneratePatientBillingRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    require_automated_billing(db, str(user.tenant_id))

    try:
        return generate_patient_billing(
            db=db,
            patient_id=payload.patient_id,
            billing_cycle_id=payload.billing_cycle_id,
            rate_schedule=payload.rate_schedule,
        )
    except BillingEngineError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# =========================================================
# CLAIM EXPORT (AUTOMATED ONLY)
# =========================================================

@router.post(
    "/export-patient-claim",
    response_model=BuildPatientClaimExportResponse,
)
def export_patient_claim(
    payload: BuildPatientClaimExportRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    require_automated_billing(db, str(user.tenant_id))

    try:
        return build_patient_claim_export(
            db=db,
            patient_id=payload.patient_id,
            billing_cycle_id=payload.billing_cycle_id,
        )
    except ClaimExportError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# =========================================================
# EDI EXPORT (AUTOMATED ONLY)
# =========================================================

@router.post(
    "/export-patient-claim-edi",
    response_model=BuildPatientClaimEDIResponse,
)
def export_patient_claim_edi(
    payload: BuildPatientClaimEDIRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    require_automated_billing(db, str(user.tenant_id))

    try:
        export_payload = build_patient_claim_export(
            db=db,
            patient_id=payload.patient_id,
            billing_cycle_id=payload.billing_cycle_id,
        )

        validation = validate_claim(export_payload)
        errors = validation.get("errors", [])
        warnings = validation.get("warnings", [])

        if errors and not payload.override_used:
            raise HTTPException(status_code=400, detail=errors)

        edi_text = build_837i_text(export_payload)

        file_path = save_edi_to_file(
            db=db,
            edi_text=edi_text,
            export_payload=export_payload,
        )

        claim_control_number = export_payload.get("claim_header", {}).get(
            "claim_control_number"
        )

        log = ClaimExportLog(
            id=str(uuid4()),
            tenant_id=export_payload.get("claim_header", {}).get("tenant_id"),
            patient_id=payload.patient_id,
            billing_cycle_id=payload.billing_cycle_id,
            file_path=file_path,
            export_type="837I",
            status="SUCCESS",
            override_used=payload.override_used,
            override_reason=payload.override_reason,
        )

        db.add(log)

        # ---------------------------------------------------------
        # Real claim lifecycle: mark the claim SENT and record the EDI
        # submission as its own batch (currently one claim per batch --
        # a future true multi-claim batch submit can group more claims
        # under the same batch_number) so it survives restarts and is
        # queryable for the Biller's Dashboard / Claims Management page.
        # ---------------------------------------------------------
        claim = db.execute(
            select(Claim)
            .where(Claim.patient_id == payload.patient_id)
            .where(Claim.billing_cycle_id == payload.billing_cycle_id)
        ).scalar_one_or_none()

        if claim is not None:
            claim_tenant_id = export_payload.get("claim_header", {}).get("tenant_id")
            batch = ClaimEdiBatch(
                id=str(uuid4()),
                tenant_id=claim_tenant_id,
                batch_number=f"EDI-{claim_control_number or uuid4()}",
                claim_count=1,
                total_amount=claim.total_charge or 0,
                file_path=file_path,
                ack_status="PENDING",
            )
            db.add(batch)
            db.flush()

            claim.status = "SENT"
            claim.claim_control_number = claim_control_number
            claim.exported_at = datetime.utcnow()
            claim.edi_batch_id = batch.id
            claim.last_status_reason = "Submitted via 837I export"

        db.commit()

        return {
            "edi_text": edi_text,
            "claim_control_number": claim_control_number,
            "billing_cycle_id": payload.billing_cycle_id,
            "patient_id": payload.patient_id,
            "file_path": file_path,
            "errors": errors,
            "warnings": warnings,
            "override_used": payload.override_used,
        }

    except (ClaimExportError, EDIBuilderError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# =========================================================
# BILLER'S DASHBOARD -- AGENCY SELECTOR
#
# The billing organization (e.g. "North East Billing") is its own tenant,
# separate from every hospice agency it bills for. Its staff pick which
# agency to work from a dropdown in the Biller's Dashboard; every other
# billing endpoint below then scopes strictly to that one selected agency.
# =========================================================

@router.get("/agencies")
def get_billable_agencies(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Agency tenants selectable in the Biller's Dashboard tenant dropdown.
    Restricted to billing-department accounts (the biller's own staff) --
    this is a roster of client agencies, not a general tenant directory.
    """
    if access_scope_for_role(getattr(user, "role", None)) != "billing":
        raise HTTPException(status_code=403, detail="Billing department access required")

    return {"agencies": list_billable_agency_tenants(db)}


# =========================================================
# BILLING READINESS (chart-completeness gate + reports)
# =========================================================

@router.get(
    "/readiness/{patient_id}",
    response_model=PatientBillingReadinessResponse,
)
def get_patient_billing_readiness(
    patient_id: str,
    service_date: date = Query(..., description="Date used to evaluate coverage/documentation, e.g. the billing cycle's start date."),
    tenant_id: UUID | None = Query(None, description="Agency tenant to evaluate. Required for billing-department accounts, which must explicitly pick an agency."),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Returns a ready/not-ready verdict for a single patient, with short
    billing-relevant blocker/warning labels only -- no raw chart content.
    """
    scoped_tenant_id = str(resolve_billing_scope_tenant_id(db, user, tenant_id))
    require_automated_billing(db, scoped_tenant_id)

    verdict = check_patient_billing_readiness(
        db,
        tenant_id=scoped_tenant_id,
        patient_id=patient_id,
        service_date=service_date,
    )

    return {
        "patient_id": verdict.patient_id,
        "period_number": verdict.period_number,
        "ready": verdict.ready,
        "blockers": verdict.blockers,
        "warnings": verdict.warnings,
    }


@router.get(
    "/readiness-report",
    response_model=TenantBillingReadinessReportResponse,
)
def get_tenant_billing_readiness_report(
    service_date: date = Query(..., description="Date used to evaluate coverage/documentation for every active patient."),
    tenant_id: UUID | None = Query(None, description="Agency tenant to evaluate. Required for billing-department accounts, which must explicitly pick an agency."),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Agency-wide "who is ready to bill" report -- every ACTIVE patient in
    the tenant with a ready/not-ready verdict and short blocker labels.
    Intended as a pre-billing checklist/alert, not a chart export: no
    clinical notes, assessment answers, or other chart content is
    included, only billing-relevant completeness flags.
    """
    scoped_tenant_id = str(resolve_billing_scope_tenant_id(db, user, tenant_id))
    require_automated_billing(db, scoped_tenant_id)

    return build_tenant_billing_readiness_report(
        db,
        tenant_id=scoped_tenant_id,
        service_date=service_date,
    )


# =========================================================
# BATCH BILLING GENERATION (PER AGENCY)
# =========================================================

@router.post(
    "/batch-generate",
    response_model=BatchGeneratePatientBillingResponse,
)
def batch_generate_patient_billing(
    payload: BatchGeneratePatientBillingRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Generates billing for every ACTIVE patient in the tenant for the given
    billing cycle, one patient at a time. Each patient is first checked
    for billing readiness (signed CTI, F2F when required, active/approved
    Plan of Care, NOE on file, resolvable payer sequence) -- patients that
    are not ready are SKIPPED (never silently billed against an
    incomplete chart) and reported back with their blocker reasons so the
    agency can fix the chart and re-run. One patient's failure never
    aborts the batch for the rest of the agency's patients.
    """
    tenant_id = str(resolve_billing_scope_tenant_id(db, user, payload.tenant_id))
    require_automated_billing(db, tenant_id)

    cycle = db.execute(
        text(
            """
            SELECT id::text AS id, tenant_id::text AS tenant_id, start_date
            FROM billing_cycles
            WHERE id = :billing_cycle_id AND tenant_id = :tenant_id
            """
        ),
        {"billing_cycle_id": payload.billing_cycle_id, "tenant_id": tenant_id},
    ).mappings().first()

    if not cycle:
        raise HTTPException(status_code=404, detail="Billing cycle not found for this tenant")

    patient_rows = db.execute(
        text(
            """
            SELECT id::text AS id, mrn
            FROM patients
            WHERE tenant_id = :tenant_id AND status = 'ACTIVE'
            ORDER BY mrn
            """
        ),
        {"tenant_id": tenant_id},
    ).mappings().all()

    results: list[dict] = []
    generated_count = 0
    skipped_count = 0
    failed_count = 0

    for row in patient_rows:
        patient_id = row["id"]

        readiness = check_patient_billing_readiness(
            db,
            tenant_id=tenant_id,
            patient_id=patient_id,
            service_date=cycle["start_date"],
        )

        if not readiness.ready:
            skipped_count += 1
            results.append(
                {
                    "patient_id": patient_id,
                    "mrn": row["mrn"],
                    "status": "SKIPPED_NOT_READY",
                    "blockers": readiness.blockers,
                    "billing_summary_id": None,
                    "error": None,
                }
            )
            continue

        try:
            generated = generate_patient_billing(
                db=db,
                patient_id=patient_id,
                billing_cycle_id=payload.billing_cycle_id,
                rate_schedule=payload.rate_schedule,
            )
            generated_count += 1
            results.append(
                {
                    "patient_id": patient_id,
                    "mrn": row["mrn"],
                    "status": "GENERATED",
                    "blockers": [],
                    "billing_summary_id": generated.get("billing_summary_id"),
                    "error": None,
                }
            )
        except BillingEngineError as exc:
            failed_count += 1
            results.append(
                {
                    "patient_id": patient_id,
                    "mrn": row["mrn"],
                    "status": "FAILED",
                    "blockers": [],
                    "billing_summary_id": None,
                    "error": str(exc),
                }
            )

    return {
        "billing_cycle_id": payload.billing_cycle_id,
        "total_patients": len(patient_rows),
        "generated_count": generated_count,
        "skipped_not_ready_count": skipped_count,
        "failed_count": failed_count,
        "results": results,
    }