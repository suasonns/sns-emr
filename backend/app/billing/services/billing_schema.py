from __future__ import annotations

from pydantic import BaseModel, Field


class GeneratePatientBillingRequest(BaseModel):
    patient_id: str
    billing_cycle_id: str

    # Optional rate schedule override for testing / payer modeling.
    # Example:
    # {
    #   "ROUTINE": "211.34",
    #   "GIP": "1123.45",
    #   "RESPITE": "487.22",
    #   "CONTINUOUS CARE": "0.00"
    # }
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