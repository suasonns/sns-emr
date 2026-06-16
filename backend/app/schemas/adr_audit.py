"""ADR/TPE audit & export schemas.

Governed by:
- backend/docs/compliance/ADR_AUDIT_RULES.md

Do not drift.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class AdrAuditStatus(str, Enum):
    FAIL = "FAIL"


class AdrAuditFinding(BaseModel):
    rule_id: str = Field(..., description="Rule identifier (A1..F1)")
    status: AdrAuditStatus = Field(default=AdrAuditStatus.FAIL)
    summary: str
    location: Optional[str] = Field(default=None, description="Entity id + relevant date")
    why_it_blocks: str
    guidance: str


class AdrAuditResult(BaseModel):
    ready: bool
    findings: List[AdrAuditFinding] = Field(default_factory=list)
    audit_ran_at: datetime
    patient_id: str
    adr_start: date
    adr_end: date
    mode: str = Field(default="ADR", description="ADR or TPE")


class AdrExportRequest(BaseModel):
    patient_id: str
    adr_start: date
    adr_end: date
    adr_mode: bool = True
    mode: str = Field(default="ADR", description="ADR or TPE")


class AdrReadinessBanner(BaseModel):
    ready: bool
    banner_text: str
    fail_count: int
    top_fail_rules: List[str] = Field(default_factory=list)
    audit: AdrAuditResult
