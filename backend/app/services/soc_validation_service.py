"""
SOCValidationService — the single, shared validation checkpoint for every
code path that establishes Start of Care (SOC).

Per the SSOT directive (docs/workflows/SourceOfTruthMatrix.md), SOC has
exactly one enforcement rule. There are two real, independently-triggered
entry points -- Path A (AdmissionGuardrailService.set_soc_datetime, manual
SOC entry) and Path B (authorize_admission, RN admission order) -- and they
are deliberately NOT merged into a single function, since they represent
different real-world triggers. Instead, both call this service so the
SAME rule enforces no matter which entry point fires.

This module contains NO SOC-writing logic. It only answers:
"is this patient allowed to have SOC established right now?"

That question is currently defined as: has staff documented Benefit Period,
Starting Cert, Admit Type, and (for TRANSFER_FROM_ANOTHER_HOSPICE) Transfer
Source + Transfer Evidence? See evaluate_soc_gate() in
app/billing/services/eligibility_workflow_service.py for the underlying
rule; this service is a thin, stable wrapper so callers never import the
billing-service internals directly.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.billing.services.eligibility_workflow_service import (
    SOC_GATE_BLOCKER_MESSAGE,
    evaluate_soc_gate,
)


class SOCValidationError(ValueError):
    """Raised when SOC establishment is attempted before prerequisites are documented."""


@dataclass(frozen=True)
class SOCValidationResult:
    ready: bool
    blockers: list[str] = field(default_factory=list)


class SOCValidationService:
    """
    Single shared SOC-establishment checkpoint for all entry points.

    Every code path that writes admission.soc_date (or patient.soc_date)
    MUST call ensure_ready() before performing that write.
    """

    @staticmethod
    def validate(db: Session, *, tenant_id: str, patient_id: str) -> SOCValidationResult:
        gate = evaluate_soc_gate(db, tenant_id=tenant_id, patient_id=patient_id)
        return SOCValidationResult(ready=gate.ready, blockers=list(gate.blockers))

    @classmethod
    def ensure_ready(cls, db: Session, *, tenant_id: str, patient_id: str) -> SOCValidationResult:
        """
        Raise SOCValidationError if SOC prerequisites are not yet documented.
        Returns the passing result otherwise so callers can inspect it if useful.
        """
        result = cls.validate(db, tenant_id=tenant_id, patient_id=patient_id)
        if not result.ready:
            raise SOCValidationError(SOC_GATE_BLOCKER_MESSAGE)
        return result
