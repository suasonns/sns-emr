from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod


class RuleOutcome(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    VIOLATION = "VIOLATION"


class RuleSeverity(str, Enum):
    WARN = "WARN"     # Advisory, never blocks
    BLOCK = "BLOCK"   # Blocking only when enforcement is enabled


class Workflow(str, Enum):
    ADMISSION = "ADMISSION"
    RECERTIFICATION = "RECERTIFICATION"
    IDG = "IDG"


@dataclass(frozen=True)
class DiagnosisItem:
    """
    Represents a diagnosis code entry (primary or secondary) with optional relatedness.
    """
    icd10: str
    description: Optional[str] = None
    is_related_to_primary: Optional[bool] = None


@dataclass
class RuleContext:
    """
    Minimal, audit-safe context passed into rule evaluation.

    Rules MUST NOT mutate context.
    Context carries patient + tenant scope and the evidence/facts required
    to make a defensible recommendation or decision.
    """
    tenant_id: Optional[str] = None
    patient_id: Optional[str] = None

    workflow: Workflow = Workflow.ADMISSION

    # Dates (use strings or date objects depending on your system)
    admission_date: Optional[Any] = None
    benefit_period_id: Optional[str] = None

    # Document provenance
    document_id: Optional[str] = None
    document_type: Optional[str] = None  # e.g., HNP/H&P, ECHO, LAB

    # Diagnoses
    primary_dx: Optional[DiagnosisItem] = None
    secondary_dx: List[DiagnosisItem] = field(default_factory=list)

    # Extracted facts (evidence graph inputs)
    # Example keys: "ef", "bnp", "nyha", "weight_loss_percent_6_months"
    facts: Dict[str, Any] = field(default_factory=dict)

    # Any extra workflow metadata
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RuleResult:
    """
    Output of a rule evaluation. This must be audit-ready.
    """
    rule_id: str
    rule_name: str
    outcome: RuleOutcome
    severity: RuleSeverity
    reason: str

    # Optional structured details for UI/audit packet
    details: Dict[str, Any] = field(default_factory=dict)

    # Optional reference to evidence (document id, snippet keys, etc.)
    evidence: Dict[str, Any] = field(default_factory=dict)


class BaseRule(ABC):
    """
    Base interface for all rules.
    Rules evaluate and return a RuleResult.
    Rules DO NOT enforce, raise, or write to DB.
    """

    rule_id: str = "UNSET_RULE_ID"
    rule_name: str = "UNSET_RULE_NAME"

    @abstractmethod
    def evaluate(self, ctx: RuleContext) -> RuleResult:
        raise NotImplementedError

    # Helper factories (consistent output)
    def pass_result(self, reason: str = "PASS", **kwargs) -> RuleResult:
        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            outcome=RuleOutcome.PASS,
            severity=RuleSeverity.WARN,
            reason=reason,
            details=kwargs.get("details", {}),
            evidence=kwargs.get("evidence", {}),
        )

    def warn_result(self, reason: str, **kwargs) -> RuleResult:
        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            outcome=RuleOutcome.WARN,
            severity=RuleSeverity.WARN,
            reason=reason,
            details=kwargs.get("details", {}),
            evidence=kwargs.get("evidence", {}),
        )

    def block_result(self, reason: str, **kwargs) -> RuleResult:
        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            outcome=RuleOutcome.VIOLATION,
            severity=RuleSeverity.BLOCK,
            reason=reason,
            details=kwargs.get("details", {}),
            evidence=kwargs.get("evidence", {}),
        )