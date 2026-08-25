from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.billing.security import require_automated_billing
from app.core.database import get_db
from app.core.security import get_current_user
from app.core.tenant_scope import resolve_billing_scope_tenant_id
from app.models.benefit_period import BenefitPeriod
from app.models.certification import Certification
from app.models.f2f_encounter import F2FEncounter
from app.models.patient import Patient
from app.models.patient_facesheet import PatientFaceSheet
from app.models.plan_of_care import PlanOfCare
from app.models.poc_physician_approval import PocPhysicianApproval

router = APIRouter(prefix="/billing", tags=["Billing POC & Certification"])


def _patient_name(first_name: str | None, middle_name: str | None, last_name: str | None) -> str | None:
    parts = [p for p in (first_name, middle_name, last_name) if p]
    return " ".join(parts) if parts else None


def _latest_certification(db: Session, tenant_id, benefit_period_id):
    return (
        db.query(Certification)
        .filter(
            Certification.tenant_id == tenant_id,
            Certification.benefit_period_id == benefit_period_id,
        )
        .order_by(Certification.signed_at.desc().nullslast(), Certification.created_at.desc())
        .first()
    )


def _latest_poc_approval(db: Session, tenant_id, poc_version_id):
    if not poc_version_id:
        return None
    return (
        db.query(PocPhysicianApproval)
        .filter(
            PocPhysicianApproval.tenant_id == tenant_id,
            PocPhysicianApproval.poc_version_id == poc_version_id,
        )
        .order_by(PocPhysicianApproval.created_at.desc())
        .first()
    )


def _latest_f2f(db: Session, tenant_id, benefit_period_id):
    return (
        db.query(F2FEncounter)
        .filter(
            F2FEncounter.tenant_id == tenant_id,
            F2FEncounter.benefit_period_id == benefit_period_id,
        )
        .order_by(F2FEncounter.encounter_date.desc())
        .first()
    )


@router.get("/poc-certification-status")
def list_poc_certification_status(
    patient_id: str | None = None,
    current_period_only: bool = Query(
        True, description="Only include each patient's current (is_current=true) benefit period."
    ),
    limit: int = Query(200, le=1000),
    tenant_id: UUID | None = Query(
        None, description="Agency tenant to view. Required for billing-department accounts, which must explicitly pick an agency."
    ),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Tenant-scoped, read-only aggregation joining ``benefit_periods`` with
    their governing ``certifications`` (CTI/recert), ``plan_of_care`` +
    latest ``poc_physician_approvals`` signature, and (when RECERT) the
    supporting ``f2f_encounters`` row -- i.e. the exact set of real records
    CMS requires to be complete before a billing-cycle can be safely
    submitted for that benefit period. No fabricated/derived documents;
    every field here traces to a real persisted row.
    """
    scoped_tenant_id = str(resolve_billing_scope_tenant_id(db, user, tenant_id))
    require_automated_billing(db, scoped_tenant_id)

    bp_query = db.query(BenefitPeriod).filter(BenefitPeriod.tenant_id == scoped_tenant_id)
    if patient_id:
        bp_query = bp_query.filter(BenefitPeriod.patient_id == patient_id)
    if current_period_only:
        bp_query = bp_query.filter(BenefitPeriod.is_current.is_(True))

    benefit_periods = (
        bp_query.order_by(BenefitPeriod.patient_id, BenefitPeriod.period_number.desc())
        .limit(limit)
        .all()
    )

    patient_ids = {bp.patient_id for bp in benefit_periods}
    patients_by_id = {
        p.id: p
        for p in db.query(Patient).filter(Patient.id.in_(patient_ids)).all()
    } if patient_ids else {}
    facesheets_by_patient = {
        fs.patient_id: fs
        for fs in db.query(PatientFaceSheet).filter(PatientFaceSheet.patient_id.in_(patient_ids)).all()
    } if patient_ids else {}

    pocs_by_patient = {}
    if patient_ids:
        for poc in db.query(PlanOfCare).filter(PlanOfCare.patient_id.in_(patient_ids), PlanOfCare.tenant_id == scoped_tenant_id).order_by(PlanOfCare.created_at.desc()).all():
            pocs_by_patient.setdefault(poc.patient_id, []).append(poc)

    results = []
    for bp in benefit_periods:
        patient = patients_by_id.get(bp.patient_id)
        facesheet = facesheets_by_patient.get(bp.patient_id)

        cert = _latest_certification(db, scoped_tenant_id, bp.id)

        poc_candidates = pocs_by_patient.get(bp.patient_id, [])
        poc = poc_candidates[0] if poc_candidates else None
        poc_version = poc.current_version if poc else None
        poc_approval = _latest_poc_approval(db, scoped_tenant_id, poc_version.id if poc_version else None)

        f2f = _latest_f2f(db, scoped_tenant_id, bp.id) if bp.benefit_type == "RECERT" else None

        results.append(
            {
                "patient_id": str(bp.patient_id),
                "patient_name": _patient_name(
                    facesheet.first_name if facesheet else None,
                    facesheet.middle_name if facesheet else None,
                    facesheet.last_name if facesheet else None,
                ),
                "mrn": patient.mrn if patient else None,
                "benefit_period": {
                    "id": str(bp.id),
                    "benefit_type": bp.benefit_type,
                    "period_number": bp.period_number,
                    "start_date": bp.start_date.isoformat() if bp.start_date else None,
                    "end_date": bp.end_date.isoformat() if bp.end_date else None,
                    "is_current": bool(bp.is_current),
                    "noe_submitted_date": bp.noe_submitted_date.isoformat() if bp.noe_submitted_date else None,
                    "noe_exception_reason": bp.noe_exception_reason,
                },
                "certification": (
                    {
                        "id": str(cert.id),
                        "cert_type": cert.cert_type,
                        "status": cert.status,
                        "signed_at": cert.signed_at.isoformat() if cert.signed_at else None,
                        "effective_date": cert.effective_date.isoformat() if cert.effective_date else None,
                        "expires_at": cert.expires_at.isoformat() if cert.expires_at else None,
                        "signed_by_role": cert.signed_by_role,
                    }
                    if cert
                    else None
                ),
                "plan_of_care": (
                    {
                        "id": str(poc.id),
                        "status": poc.status,
                        "current_version_number": poc_version.version_number if poc_version else None,
                        "physician_approval_status": poc_approval.approval_status if poc_approval else None,
                        "physician_approval_date": (
                            poc_approval.approval_date.isoformat()
                            if poc_approval and poc_approval.approval_date
                            else None
                        ),
                        "physician_name": poc_approval.physician_name if poc_approval else None,
                    }
                    if poc
                    else None
                ),
                "f2f_encounter": (
                    {
                        "id": str(f2f.id),
                        "encounter_date": f2f.encounter_date.isoformat() if f2f.encounter_date else None,
                        "status": f2f.status,
                        "performed_by_role": f2f.performed_by_role,
                        "attested_at": f2f.attested_at.isoformat() if f2f.attested_at else None,
                    }
                    if f2f
                    else None
                ),
                "billing_ready": bool(
                    cert
                    and cert.status == "FINALIZED"
                    and poc_approval
                    and poc_approval.approval_status == "PHYSICIAN_APPROVED"
                    and (bp.benefit_type != "RECERT" or (f2f and f2f.status == "FINALIZED"))
                ),
            }
        )

    return {
        "tenant_id": scoped_tenant_id,
        "count": len(results),
        "poc_certification_status": results,
    }
