from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.db_tenant_dependency import get_db_tenant
from app.services.audit_logger import log_event
from app.services.regulatory_report_service import (
    certify_and_lock_report,
    ReportNotFound,
    ReportLocked,
)
from app.core.security_deps import get_current_user_id


router = APIRouter(
    prefix="/regulatory-reports",
    tags=["Regulatory Reports"],
)


# ---------------------------------------------------------------------
# RESPONSE MODEL (AUDIT SAFE)
# ---------------------------------------------------------------------
class RegulatoryReportResponse(BaseModel):
    request_id: str
    timestamp: str
    report_id: str
    status: str
    certified_at: Optional[str]
    certified_by: Optional[str]
    integrity_hash: Optional[str]


# ---------------------------------------------------------------------
# ENDPOINT
# ---------------------------------------------------------------------
@router.post(
    "/{report_id}/certify",
    response_model=RegulatoryReportResponse,
    status_code=status.HTTP_200_OK,
)
def certify_report(
    report_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db_tenant),  # ✅ CRITICAL FIX
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """
    Certifies and locks a regulatory report.

    - Prevents further modification
    - Generates integrity hash
    - Required for survey / ADR defense
    """

    request_id = str(uuid.uuid4())

    try:
        report = certify_and_lock_report(db, report_id, user_id)

    except ReportNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    except ReportLocked as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to certify report",
        )

    # -----------------------------------------------------------------
    # ✅ ENTERPRISE AUDIT (BUSINESS EVENT)
    # -----------------------------------------------------------------
    tenant_id = getattr(request.state, "tenant_id", None)

    log_event(
        request_id=request_id,
        user_id=str(user_id),
        tenant_id=str(tenant_id) if tenant_id else None,
        role=None,
        action="REG_REPORT_CERTIFIED",
        entity_type="regulatory_report",
        entity_id=str(report_id),
        ip=request.client.host if request.client else None,
        metadata={
            "status": report.status,
            "certified_at": report.certified_at.isoformat()
            if report.certified_at
            else None,
        },
        db=db,
        commit=True,  # ✅ IMPORTANT
    )

    return {
        "request_id": request_id,
        "timestamp": datetime.utcnow().isoformat(),
        "report_id": str(report.id),
        "status": report.status,
        "certified_at": (
            report.certified_at.isoformat() if report.certified_at else None
        ),
        "certified_by": (
            str(report.certified_by) if report.certified_by else None
        ),
        "integrity_hash": report.integrity_hash,
    }
