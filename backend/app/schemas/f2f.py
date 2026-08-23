# app/schemas/f2f.py

"""
Authoritative Face-to-Face (F2F) request/response contract.

Consolidated 2026-08-22: this module previously held a stale, unused,
minimal F2FCreateRequest (never imported by any router, test, or
Alembic script — confirmed by repo-wide search). The complete, active
contract actually used by app/api/f2f.py was instead defined inline in
that file. This module now holds the single authoritative definition;
app/api/f2f.py imports from here. No field, type, default, or
validator was changed — this is a pure move, not a behavior change.
"""

from __future__ import annotations

from datetime import date
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class F2FCreateRequest(BaseModel):
    patient_id: UUID
    benefit_period_id: UUID
    encounter_date: date

    # performed_by_role is NOT accepted from the request — the endpoint
    # always derives it from the authenticated user's own role, so a
    # caller can never record an unauthorized discipline as the F2F
    # performer. Retained here only for backward-compatible clients;
    # any client-supplied value is ignored.
    performed_by_role: Optional[str] = None

    summary: Optional[str] = Field(default=None, max_length=5000)
    clinical_decline_summary: Optional[str] = Field(default=None, max_length=5000)

    # Functional scoring
    kps_score: Optional[int] = None
    pps_score_previous: Optional[int] = None
    pps_score_current: Optional[int] = None
    ecog_score_previous: Optional[int] = Field(default=None, ge=0, le=5)
    ecog_score_current: Optional[int] = Field(default=None, ge=0, le=5)

    # Disease scoring
    fast_score: Optional[str] = None
    nyha_class: Optional[str] = None

    # ADL / decline
    adl_dependency_level: Optional[str] = None
    adl_dependency_count: Optional[int] = None
    is_bedbound: Optional[bool] = None

    # Objective decline indicators
    weight_loss_lbs: Optional[float] = None
    oral_intake_decline: Optional[bool] = None
    dysphagia: Optional[bool] = None
    hospitalizations_30d: Optional[int] = None
    oxygen_lpm_previous: Optional[float] = None
    oxygen_lpm_current: Optional[float] = None

    primary_diagnosis: Optional[str] = None
    secondary_conditions: Optional[str] = None


class F2FCreateResponse(BaseModel):
    id: UUID
    status: str
    encounter_date: date


class F2FFinalizeRequest(BaseModel):
    # Used when NP performed the F2F and physician review/attestation is captured on the encounter.
    attestation_summary: Optional[str] = Field(default=None, max_length=5000)


class F2FFinalizeResponse(BaseModel):
    id: UUID
    status: str
    finalized_at: Optional[str]
