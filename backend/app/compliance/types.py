from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Sequence, Literal
from uuid import UUID


Regulator = Literal["CMS", "ACHC", "CDPH", "TJC", "CHAP"]
EvidenceType = Literal["VISIT", "NOTE"]


@dataclass(frozen=True)
class RuleMeta:
    regulator: Regulator
    code: str                 # e.g., "CMS-418.56-POC-UPDATE"
    title: str                # human title
    version: str              # e.g., "2026.05"
    effective_date: str       # ISO date string
    reference: str            # survey citation / internal mapping
    description: str          # short purpose statement


@dataclass(frozen=True)
class Obligation:
    """
    A structured output from a compliance rule.

    The task engine consumes this and performs DB writes.
    """
    task_type: str
    origin: str
    due_date: datetime
    evidence_required: Sequence[EvidenceType]
    patient_id: UUID
    # Optional linkage
    visit_id: Optional[UUID] = None
    benefit_period_id: Optional[UUID] = None
    notes: Optional[str] = None