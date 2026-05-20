# app/services/admission_guardrails_service.py

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.documentation_assessment import DocumentationAssessment
from app.services.tenant_settings_service import TenantSettingsService
from app.constants.guardrail_messages import RN_DOCUMENTATION_GUIDANCE


@dataclass(frozen=True)
class GuardrailOutcome:
    status: str
    severity: str
    flags: List[str]
    hard_stop: bool
    requires_md_review: bool
    ui: Dict[str, Any]


class AdmissionGuardrailsService:
    """
    SNS Hospice Admission Guardrails (Decision Support Only)

    - Provides CMS LCD documentation guidance
    - Identifies documentation risk
    - Recommends MD review when appropriate
    - NEVER blocks admission
    """

    SERVICE_VERSION = "v1.0"

    LCD_BAD = {"INCOMPLETE", "INCONSISTENT", "NARRATIVE_REQUIRED"}

    SEVERITY_ORDER = ["INFO", "WARNING", "HIGH", "CRITICAL"]
    MODES = {"OFF", "SILENT", "GUIDANCE", "STRICT"}

    @staticmethod
    def assess_admission(
        db: Session,
        *,
        admission: Any,
        user_id: str,
        tenant_id: str,
        patient_id: str,
        lcd_status: Optional[str] = None,
        narrative_text: Optional[str] = None,
        has_measurable_decline: Optional[bool] = None,
        flush: bool = True,
    ) -> Dict[str, Any]:

        if db is None:
            raise ValueError("db session is required")
        if not tenant_id:
            raise ValueError("tenant_id is required")
        if not user_id:
            raise ValueError("user_id is required")
        if not patient_id:
            raise ValueError("patient_id is required")
        if admission is None:
            raise ValueError("admission object is required")

        mode = AdmissionGuardrailsService._safe_get_guardrail_mode(db, tenant_id)
        if mode not in AdmissionGuardrailsService.MODES:
            mode = "GUIDANCE"

        narrative = (narrative_text or "").strip()

        flags: List[str] = []
        severity = "INFO"
        requires_md_review = False

        if not narrative:
            flags.append("MISSING_ELIGIBILITY_NARRATIVE")
            severity = AdmissionGuardrailsService._escalate(severity, "HIGH")
        elif len(narrative) < 200:
            flags.append("WEAK_ELIGIBILITY_NARRATIVE")
            severity = AdmissionGuardrailsService._escalate(severity, "WARNING")

        if not has_measurable_decline:
            flags.append("NO_MEASURABLE_EVIDENCE_OF_DECLINE")
            severity = AdmissionGuardrailsService._escalate(severity, "HIGH")

        if lcd_status and lcd_status in AdmissionGuardrailsService.LCD_BAD:
            flags.append(f"LCD_STATUS_{lcd_status}")
            severity = AdmissionGuardrailsService._escalate(severity, "CRITICAL")

        if severity == "CRITICAL":
            requires_md_review = True

        status = AdmissionGuardrailsService._map_status(severity)

        if mode != "OFF":
            AdmissionGuardrailsService._persist_assessment(
                db=db,
                admission=admission,
                tenant_id=tenant_id,
                user_id=user_id,
                patient_id=patient_id,
                status=status,
                severity=severity,
                flags=flags,
                requires_md_review=requires_md_review,
            )

            AdmissionGuardrailsService._audit(
                db=db,
                action="ADMISSION_RISK_ASSESSMENT",
                entity_type="ADMISSION",
                entity_id=str(getattr(admission, "id", "") or ""),
                user_id=user_id,
                tenant_id=tenant_id,
                details={
                    "status": status,
                    "severity": severity,
                    "flags": flags,
                    "requires_md_review": requires_md_review,
                    "rn_explanation": RN_DOCUMENTATION_GUIDANCE,
                },
            )

            if flush:
                db.flush()

        return {
            "status": status,
            "severity": severity,
            "flags": flags,
            "requires_md_review": requires_md_review,
            "rn_explanation": RN_DOCUMENTATION_GUIDANCE,
            "guardrail_mode": mode,
            "service_version": AdmissionGuardrailsService.SERVICE_VERSION,
        }

    # -----------------------
    # Helpers
    # -----------------------

    @staticmethod
    def _safe_get_guardrail_mode(db: Session, tenant_id: str) -> str:
        try:
            mode = TenantSettingsService.get_guardrail_mode(db, tenant_id)
            if isinstance(mode, str):
                return mode.strip().upper()
        except Exception:
            pass
        return "GUIDANCE"

    @staticmethod
    def _escalate(current: str, new: str) -> str:
        order = AdmissionGuardrailsService.SEVERITY_ORDER
        return order[max(order.index(current), order.index(new))]

    @staticmethod
    def _map_status(severity: str) -> str:
        if severity == "CRITICAL":
            return "INCONSISTENT"
        if severity == "HIGH":
            return "INCOMPLETE"
        if severity == "WARNING":
            return "NARRATIVE_REQUIRED"
        return "SUPPORTED"