from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.rules.base import RuleContext, Workflow, DiagnosisItem
from app.services.rules_dry_run import dry_run_rules
from app.dependencies.tenant import inject_tenant
from app.core.database import get_db  # or your canonical get_db path

router = APIRouter(prefix="/rules", tags=["Rules"])


@router.post("/dry-run")
def dry_run(
    payload: dict,
    db: Session = Depends(get_db),
    tenant=Depends(inject_tenant),
):
    # Robust tenant id extraction (handles object or string return types)
    tenant_id = None
    if tenant is not None:
        tenant_id = getattr(tenant, "id", None) or getattr(tenant, "tenant_id", None) or (tenant if isinstance(tenant, str) else None)

    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context missing (inject_tenant returned no tenant_id)")

    ctx = RuleContext(
        tenant_id=str(tenant_id),
        patient_id=payload.get("patient_id"),
        workflow=Workflow(payload.get("workflow", "ADMISSION")),
        primary_dx=DiagnosisItem(icd10=payload.get("primary_dx", "")),
        facts=payload.get("facts", {}),
    )

    report = dry_run_rules(ctx, db=db)

    return {
        "context": {
            "tenant_id": ctx.tenant_id,
            "patient_id": ctx.patient_id,
            "workflow": ctx.workflow.value,
            "primary_dx": ctx.primary_dx.icd10 if ctx.primary_dx else None,
            "facts": ctx.facts,
        },
        "summary": report["summary"],
        "results": report["results"],
    }