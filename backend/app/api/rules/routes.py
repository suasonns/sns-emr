from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Any, Dict, Optional, List
from datetime import datetime
import uuid

from app.rules.base import RuleContext, Workflow, DiagnosisItem
from app.services.rules_dry_run import dry_run_rules
from app.db_tenant_dependency import get_db_tenant
from app.core.security import get_current_user


router = APIRouter(
    prefix="/rules",
    tags=["Rules"],
)

# ---------------------------------------------------------------------
# REQUEST MODEL (VALIDATION + SWAGGER)
# ---------------------------------------------------------------------

class DryRunRequest(BaseModel):
    patient_id: Optional[str] = Field(None)
    workflow: str = Field(default="ADMISSION")
    primary_dx: Optional[str] = Field(default="")
    facts: Dict[str, Any] = Field(default_factory=dict)

# ---------------------------------------------------------------------
# RESPONSE MODEL (STRICT + AUDIT FRIENDLY)
# ---------------------------------------------------------------------

class DryRunResponse(BaseModel):
    request_id: str
    timestamp: str
    context: Dict[str, Any]
    summary: Dict[str, Any]
    results: List[Any]


class ICDRecommendationRequest(BaseModel):
    text: str = Field(default="", description="Clinical documentation text to scan for diagnosis candidates")
    patient_id: Optional[str] = Field(default=None, description="Optional patient id to enrich suggestions with real diagnosis and note evidence")
    max_results: int = Field(default=5, ge=1, le=10)


class ICDRecommendationResponse(BaseModel):
    suggestions: List[Dict[str, Any]]
    guardrails: Dict[str, Any]
    evidence: Optional[Dict[str, Any]] = None


# ---------------------------------------------------------------------
# ROUTE
# ---------------------------------------------------------------------

@router.post(
    "/icd-recommendations",
    response_model=ICDRecommendationResponse,
    status_code=status.HTTP_200_OK,
)
def icd_recommendations(
    payload: ICDRecommendationRequest,
    db: Session = Depends(get_db_tenant),
    user=Depends(get_current_user),
):
    """Return recommendation-only ICD candidates based on clinical evidence text and any linked patient evidence."""
    from app.services.icd_intelligence import gather_patient_evidence, primary_dx_guardrails, recommend_icd_candidates

    evidence = gather_patient_evidence(
        db,
        payload.patient_id,
        tenant_id=getattr(user, "tenant_id", None),
    )
    suggestions = recommend_icd_candidates(
        payload.text,
        max_results=payload.max_results,
        patient_evidence=evidence if evidence.get("text") else None,
    )

    return {
        "suggestions": suggestions,
        "guardrails": primary_dx_guardrails(),
        "evidence": {
            "patient_id": payload.patient_id,
            "source_count": evidence.get("source_count", 0),
            "diagnosis_sources": evidence.get("diagnosis_sources", []),
            "clinical_notes": evidence.get("clinical_notes", []),
            "text": evidence.get("text", ""),
        },
    }


@router.post(
    "/dry-run",
    response_model=DryRunResponse,
    status_code=status.HTTP_200_OK,
)
def dry_run(
    payload: DryRunRequest,
    db: Session = Depends(get_db_tenant),
    user=Depends(get_current_user),
):
    """
    Executes rules engine in non-persistent (dry-run) mode.

    Enterprise guarantees:
    - Tenant derived from authenticated identity
    - Tenant-scoped DB session
    - No DB mutation
    - Safe for CMS / ADR simulation
    """

    # -------------------------------------------------------------
    # TENANT CONTEXT (AUTHORITATIVE)
    # -------------------------------------------------------------
    tenant_id = user.tenant_id
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authenticated user missing tenant_id",
        )

    # -------------------------------------------------------------
    # SAFE WORKFLOW PARSING
    # -------------------------------------------------------------
    try:
        workflow_enum = Workflow(payload.workflow.upper())
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid workflow: {payload.workflow}",
        )

    # -------------------------------------------------------------
    # BUILD RULE CONTEXT
    # -------------------------------------------------------------
    ctx = RuleContext(
        tenant_id=str(tenant_id),
        patient_id=payload.patient_id,
        workflow=workflow_enum,
        primary_dx=DiagnosisItem(icd10=payload.primary_dx or ""),
        facts=payload.facts or {},
    )

    request_id = str(uuid.uuid4())

    # -------------------------------------------------------------
    # EXECUTE RULES (SAFE WRAPPER)
    # -------------------------------------------------------------
    try:
        report = dry_run_rules(ctx, db=db)
    except Exception:
        # Do not leak internal rule engine errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Rules engine execution failed",
        )

    # -------------------------------------------------------------
    # RESPONSE (AUDIT FRIENDLY)
    # -------------------------------------------------------------
    return {
        "request_id": request_id,
        "timestamp": datetime.utcnow().isoformat(),
        "context": {
            "tenant_id": ctx.tenant_id,
            "patient_id": ctx.patient_id,
            "workflow": ctx.workflow.value,
            "primary_dx": ctx.primary_dx.icd10 if ctx.primary_dx else None,
            "facts": ctx.facts,
        },
        "summary": report.get("summary", {}),
        "results": report.get("results", []),
    }