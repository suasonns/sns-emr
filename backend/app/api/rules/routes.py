from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Any, Dict, Optional, List
from datetime import datetime
import uuid

from app.rules.base import RuleContext, Workflow, DiagnosisItem
from app.services.rules_dry_run import dry_run_rules
from app.dependencies.tenant import inject_tenant
from app.core.database import get_db


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
    results: List[Any]  # enforce list for predictability


# ---------------------------------------------------------------------
# ROUTE
# ---------------------------------------------------------------------

@router.post(
    "/dry-run",
    response_model=DryRunResponse,
    status_code=status.HTTP_200_OK,
)
def dry_run(
    payload: DryRunRequest,
    db: Session = Depends(get_db),
    tenant=Depends(inject_tenant),
):
    """
    Executes rules engine in non-persistent mode.

    - Safe for simulation
    - No DB mutation
    - Used for ADR / CMS validation scenarios
    """

    # -------------------------------------------------------------
    # TENANT SAFETY (STRICT)
    # -------------------------------------------------------------
    tenant_id = None

    if tenant is not None:
        tenant_id = (
            getattr(tenant, "id", None)
            or getattr(tenant, "tenant_id", None)
            or (tenant if isinstance(tenant, str) else None)
        )

    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant context missing (inject_tenant returned no tenant_id)",
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
    # BUILD CONTEXT
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
        # DO NOT expose internal errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Rules engine execution failed",
        )

    # -------------------------------------------------------------
    # RESPONSE
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