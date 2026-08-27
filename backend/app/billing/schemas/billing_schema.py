from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# =========================================================
# BILLING CYCLE (GET-OR-CREATE)
# =========================================================

class GetOrCreateBillingCycleRequest(BaseModel):
    month: int = Field(ge=1, le=12)
    year: int = Field(ge=2000, le=2100)


class BillingCycleResponse(BaseModel):
    id: str
    tenant_id: str
    month: int
    year: int
    start_date: str
    end_date: str
    status: str
    created_at: str


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
    provider: Dict[str, Any]
    attending_provider: Dict[str, Any]
    claim_lines: List[Dict[str, Any]]
    export_metadata: Dict[str, Any]


# =========================================================
# BILLING READINESS (chart-completeness gate)
# =========================================================

class PatientBillingReadinessResponse(BaseModel):
    patient_id: str
    period_number: Optional[int]
    ready: bool
    blockers: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class TenantBillingReadinessPatientRow(BaseModel):
    patient_id: str
    mrn: str
    period_number: Optional[int]
    ready: bool
    blockers: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class TenantBillingReadinessReportResponse(BaseModel):
    tenant_id: str
    service_date: str
    total_patients: int
    ready_count: int
    not_ready_count: int
    patients: List[TenantBillingReadinessPatientRow]


# =========================================================
# BATCH BILLING GENERATION (PER AGENCY)
# =========================================================

class BatchGeneratePatientBillingRequest(BaseModel):
    billing_cycle_id: str
    rate_schedule: Optional[Dict[str, Any]] = Field(default=None)
    # Agency tenant to run the batch for. Required for billing-department
    # accounts (the biller's staff), which must explicitly pick an agency
    # from the Biller's Dashboard tenant dropdown; ignored/validated
    # against the caller's own tenant for ordinary agency users.
    tenant_id: Optional[str] = Field(default=None)


class BatchGeneratePatientResult(BaseModel):
    patient_id: str
    mrn: str
    status: str  # GENERATED | SKIPPED_NOT_READY | FAILED
    blockers: List[str] = Field(default_factory=list)
    billing_summary_id: Optional[str] = None
    error: Optional[str] = None


class BatchGeneratePatientBillingResponse(BaseModel):
    billing_cycle_id: str
    total_patients: int
    generated_count: int
    skipped_not_ready_count: int
    failed_count: int
    results: List[BatchGeneratePatientResult]

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