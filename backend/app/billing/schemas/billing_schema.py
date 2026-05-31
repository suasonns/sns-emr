from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# =========================================================
# BILLING GENERATION
# =========================================================

class GeneratePatientBillingRequest(BaseModel):
    patient_id: str
    billing_cycle_id: str
    rate_schedule: Optional[Dict[str, Any]] = Field(default=None)


class GeneratePatientBillingResponse(BaseModel):
    billing_summary_id: str
    patient_id: str
    billing_cycle_id: str

    # ✅ billing state
    status: str
    risk_score: int

    # ✅ metrics
    units: int
    total_minutes: int

    # ✅ core outputs
    loc_summary: Dict[str, Any]
    loc_segments: List[Dict[str, Any]]
    claim_lines: List[Dict[str, Any]]
    revenue_summary: Dict[str, Any]


# =========================================================
# CLAIM EXPORT (JSON STRUCTURE)
# =========================================================

class BuildPatientClaimExportRequest(BaseModel):
    patient_id: str
    billing_cycle_id: str


class BuildPatientClaimExportResponse(BaseModel):
    claim_header: Dict[str, Any]
    patient: Dict[str, Any]
    diagnosis: Dict[str, Any]
    payer: Dict[str, Any]
    claim_lines: List[Dict[str, Any]]
    export_metadata: Dict[str, Any]


# =========================================================
# EDI EXPORT (ALERT + OVERRIDE SYSTEM)
# =========================================================

class BuildPatientClaimEDIRequest(BaseModel):
    patient_id: str
    billing_cycle_id: str

    # ✅ OVERRIDE SYSTEM (CRITICAL)
    override_used: bool = False
    override_reason: Optional[str] = None


class BuildPatientClaimEDIResponse(BaseModel):
    edi_text: str
    claim_control_number: str
    billing_cycle_id: str
    patient_id: str

    # ✅ ALERT SYSTEM (FRONTEND CONSUMES THIS)
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)

    # ✅ AUDIT VISIBILITY
    override_used: bool = False