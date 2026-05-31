from __future__ import annotations

from pydantic import BaseModel, Field


class GeneratePatientBillingRequest(BaseModel):
    patient_id: str
    billing_cycle_id: str
    rate_schedule: dict | None = Field(default=None)


class GeneratePatientBillingResponse(BaseModel):
    billing_summary_id: str
    patient_id: str
    billing_cycle_id: str
    status: str
    risk_score: int
    units: int
    total_minutes: int
    loc_summary: dict
    loc_segments: list[dict]
    claim_lines: list[dict]
    revenue_summary: dict


class BuildPatientClaimExportRequest(BaseModel):
    patient_id: str
    billing_cycle_id: str


class BuildPatientClaimExportResponse(BaseModel):
    claim_header: dict
    patient: dict
    diagnosis: dict
    payer: dict
    claim_lines: list[dict]
    export_metadata: dict


class BuildPatientClaimEDIRequest(BaseModel):
    patient_id: str
    billing_cycle_id: str


class BuildPatientClaimEDIResponse(BaseModel):
    edi_text: str
    claim_control_number: str
    billing_cycle_id: str
    patient_id: str
