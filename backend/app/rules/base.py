from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional
from abc import ABC, abstractmethod
from datetime import datetime, date
from uuid import UUID


# =========================================================
# ENUMS
# =========================================================

class RuleOutcome(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    VIOLATION = "VIOLATION"


class RuleSeverity(str, Enum):
    WARN = "WARN"      # Advisory, never blocks
    BLOCK = "BLOCK"    # Blocking when enforcement enabled


class Workflow(str, Enum):
    ADMISSION = "ADMISSION"
    RECERTIFICATION = "RECERTIFICATION"
    IDG = "IDG"


# =========================================================
# DIAGNOSIS MODEL
# =========================================================

@dataclass(frozen=True)
class DiagnosisItem:
    """
    Represents a diagnosis entry (primary or secondary).
    """
    icd10: str
    description: Optional[str] = None
    is_related_to_primary: Optional[bool] = None


# =========================================================
# RULE CONTEXT (IMMUTABLE)
# =========================================================

@dataclass(frozen=True)
class RuleContext:
    """
    Audit-safe evaluation context.

    Rules MUST NOT mutate this object.
    """

    # Identity
    tenant_id: Optional[UUID] = None
    patient_id: Optional[UUID] = None

    workflow: Workflow = Workflow.ADMISSION

    # Dates
    admission_date: Optional[date] = None
    benefit_period_id: Optional[UUID] = None

    # Document provenance
    document_id: Optional[UUID] = None
    document_type: Optional[str] = None

    # Diagnoses
    primary_dx: Optional[DiagnosisItem] = None
    secondary_dx: List[DiagnosisItem] = field(default_factory=list)

    # Evidence (structured inputs only)
    facts: Dict[str, object] = field(default_factory=dict)

    # Execution metadata (important for tracing)
    meta: Dict[str, object] = field(default_factory=dict)


# =========================================================
# RULE RESULT (AUDIT READY)
# =========================================================

@dataclass(frozen=True)
class RuleResult:
    """
    Output of rule evaluation.

    MUST be fully audit traceable.
    """

    rule_id: str
    rule_name: str

    outcome: RuleOutcome
    severity: RuleSeverity

    reason: str

    # TIMESTAMP (REQUIRED FOR AUDIT)
    created_at: datetime

    # Optional structured metadata
    details: Dict[str, object] = field(default_factory=dict)

    # Evidence references (IDs, keys, etc.)
    evidence: Dict[str, object] = field(default_factory=dict)

    # Traceability
    regulator: Optional[str] = None
    rule_version: Optional[str] = None


# =========================================================
# BASE RULE INTERFACE
# =========================================================

class BaseRule(ABC):
    """
    Base interface for all rules.
    """

    rule_id: str = "UNSET_RULE_ID"
    rule_name: str = "UNSET_RULE_NAME"

    regulator: Optional[str] = None
    version: Optional[str] = None

    @abstractmethod
    def evaluate(self, ctx: RuleContext) -> RuleResult:
        raise NotImplementedError

    # =====================================================
    # HELPER OUTPUTS (STANDARDIZED)
    # =====================================================

    def _base_result(
        self,
        outcome: RuleOutcome,
        severity: RuleSeverity,
        reason: str,
        **kwargs,
    ) -> RuleResult:
        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            outcome=outcome,
            severity=severity,
            reason=reason,
            created_at=datetime.utcnow(),
            details=kwargs.get("details", {}),
            evidence=kwargs.get("evidence", {}),
            regulator=self.regulator,
            rule_version=self.version,
        )

    def pass_result(self, reason: str = "PASS", **kwargs) -> RuleResult:
        return self._base_result(
            RuleOutcome.PASS,
            RuleSeverity.WARN,
            reason,
            **kwargs,
        )

    def warn_result(self, reason: str, **kwargs) -> RuleResult:
        return self._base_result(
            RuleOutcome.WARN,
            RuleSeverity.WARN,
            reason,
            **kwargs,
        )

    def block_result(self, reason: str, **kwargs) -> RuleResult:
        return self._base_result(
            RuleOutcome.VIOLATION,
            RuleSeverity.BLOCK,
            reason,
            **kwargs,
        )