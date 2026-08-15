from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, date, UTC
from typing import Optional, Sequence, Literal, Dict, Any
from uuid import UUID

# =========================================================
# CONTROLLED VOCABULARIES
# =========================================================

Regulator = Literal["CMS", "ACHC", "CDPH", "TJC", "CHAP"]

EvidenceType = Literal["VISIT", "NOTE"]

TaskType = Literal[
    "POC_UPDATE",
    "VISIT_REQUIRED",
    "DOCUMENTATION",
    "AUDIT_REVIEW",
    "FOLLOW_UP",
]

OriginType = Literal[
    "rule_engine",
    "rule_engine.cms.poc_update",
    "rule_engine.cms.evidence",
    "manual",
    "system",
]


# =========================================================
# RULE METADATA (IMMUTABLE / AUDIT-FRIENDLY)
# =========================================================

@dataclass(frozen=True)
class RuleMeta:
    regulator: Regulator
    code: str                  # e.g., "CMS-418.56-POC-UPDATE"
    title: str                 # human readable
    version: str               # e.g., "2026.05"
    effective_date: date
    reference: str             # survey citation / policy reference
    description: str           # purpose statement

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# =========================================================
# OBLIGATION (TASK ENGINE INPUT)
# =========================================================

@dataclass(frozen=True)
class Obligation:
    """
    Structured output from a compliance rule.

    The task engine consumes this object and performs persistence separately.
    This class itself performs no DB writes.
    """

    # Rule traceability
    rule_code: str
    regulator: Regulator

    # Task details
    task_type: TaskType
    origin: OriginType

    # Timing
    created_at: datetime
    due_date: datetime

    # Required evidence
    evidence_required: Sequence[EvidenceType]

    # Entity linkage
    patient_id: UUID

    # Optional tenant/multi-entity linkage
    tenant_id: Optional[UUID] = None
    visit_id: Optional[UUID] = None
    benefit_period_id: Optional[UUID] = None

    # Optional message surfaced to user / audit packet
    notes: Optional[str] = None

    # Optional execution trace for diagnostics / replay
    execution_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)