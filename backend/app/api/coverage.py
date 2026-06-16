from __future__ import annotations

from uuid import uuid4
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.service_coverage_decision import ServiceCoverageDecision
from app.services.coverage_resolver import resolve_claim_route
from app.services.coverage_audit_logger import log_coverage_audit

router = APIRouter(prefix="/coverage", tags=["Coverage"])


@router.post("/decide")
def decide_coverage(
    patient_id: str,
    tenant_id: str,
    service_type: str,
    coverage_intent: str,
    decision_reason: str | None = None,

    db: Session = Depends(get_db),
):
    """
    ✅ CORE ENTRY POINT FOR INTENT-BASED BILLING
    """

    decision_id = str(uuid4())

    route = resolve_claim_route(
        db=db,
        tenant_id=tenant_id,
        patient_id=patient_id,
        service_type=service_type,
        coverage_intent=coverage_intent,
    )

    decision = ServiceCoverageDecision(
        id=decision_id,
        tenant_id=tenant_id,
        patient_id=patient_id,
        service_type=service_type,
        coverage_intent=coverage_intent,
        financial_responsibility=route["financial_responsibility"],
        decision_reason=decision_reason,
        selected_insurance_id=(
            route["selected_insurance"]["id"]
            if route["selected_insurance"]
            else None
        ),
    )

    db.add(decision)
    db.commit()

    # ✅ AUDIT LOG
    log_coverage_audit(
        db=db,
        tenant_id=tenant_id,
        action="COVERAGE_INTENT_SET",
        entity_type="service_coverage_decision",
        entity_id=decision_id,
        user_id=None,
        role="SYSTEM",
        request_id=None,
        ip_address=None,
        metadata={
            "patient_id": patient_id,
            "service_type": service_type,
            "coverage_intent": coverage_intent,
            "financial_responsibility": route["financial_responsibility"],
        },
    )

    return {
        "decision_id": decision_id,
        "financial_responsibility": route["financial_responsibility"],
        "insurance": route["selected_insurance"],
    }