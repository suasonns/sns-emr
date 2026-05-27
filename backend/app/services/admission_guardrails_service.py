from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from datetime import datetime

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
    Enterprise Hospice Admission Guardrails (Decision Support Only)

    - Deterministic decision support
    - CMS / ACHC / CHAP survey‑defensible
    - flush=False => NO persistence, NO audit (unit tests / dry run)
    """

    SERVICE_VERSION = "v1.1"

    LCD_BAD = {"INCOMPLETE", "INCONSISTENT", "NARRATIVE_REQUIRED"}

    SEVERITY_ORDER = ["INFO", "WARNING", "HIGH", "CRITICAL"]
    MODES = {"OFF", "SILENT", "GUIDANCE", "STRICT"}

    @staticmethod
    def assess_admission(
        *,
        db: Session,
        admission: Any,
        tenant_id: str,
        patient_id: str,
        user_id: str,
        lcd_status: Optional[str] = None,
        narrative_text: Optional[str] = None,
        has_measurable_decline: Optional[bool] = None,
        flush: bool = True,
    ) -> Dict[str, Any]:
        """
        Perform admission documentation risk assessment.

        flush=False => decision support only (deterministic, no DB side effects)
        flush=True  => persist assessment + audit (production behavior)
        """

        # ---- Preconditions ----
        if not db:
            raise RuntimeError("db session is required")
        if not tenant_id:
            raise RuntimeError("tenant_id is required")
        if not user_id:
            raise RuntimeError("user_id is required")
        if not patient_id:
            raise RuntimeError("patient_id is required")
        if admission is None:
            raise RuntimeError("admission object is required")

        mode = AdmissionGuardrailsService._get_guardrail_mode(db, tenant_id)

        narrative = (narrative_text or "").strip()

        flags: List[str] = []
        severity = "INFO"
        requires_md_review = False

        # ---- Narrative checks ----
        if not narrative:
            flags.append("MISSING_ELIGIBILITY_NARRATIVE")
            severity = AdmissionGuardrailsService._escalate(severity, "HIGH")
        elif len(narrative) < 200:
            flags.append("WEAK_ELIGIBILITY_NARRATIVE")
            severity = AdmissionGuardrailsService._escalate(severity, "WARNING")

        # ---- Decline evidence ----
        if not has_measurable_decline:
            flags.append("NO_MEASURABLE_EVIDENCE_OF_DECLINE")
            severity = AdmissionGuardrailsService._escalate(severity, "HIGH")

        # ---- LCD status ----
        if lcd_status and lcd_status in AdmissionGuardrailsService.LCD_BAD:
            flags.append(f"LCD_STATUS_{lcd_status}")
            severity = AdmissionGuardrailsService._escalate(severity, "CRITICAL")

        if severity == "CRITICAL":
            requires_md_review = True

        status = AdmissionGuardrailsService._map_status(severity)

        # ---- Persistence & audit (ONLY when flush=True) ----
        if mode != "OFF" and flush:
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

            admission_id = (
                admission.get("id")
                if isinstance(admission, dict)
                else getattr(admission, "id", "")
            )

            AdmissionGuardrailsService._audit(
                db=db,
                action="ADMISSION_RISK_ASSESSMENT",
                entity_type="ADMISSION",
                entity_id=str(admission_id or ""),
                tenant_id=tenant_id,
                user_id=user_id,
                details={
                    "status": status,
                    "severity": severity,
                    "flags": flags,
                    "requires_md_review": requires_md_review,
                    "rn_explanation": RN_DOCUMENTATION_GUIDANCE,
                },
            )

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
    def _get_guardrail_mode(db: Session, tenant_id: str) -> str:
        try:
            mode = TenantSettingsService.get_guardrail_mode(db, tenant_id)
            if isinstance(mode, str) and mode.strip().upper() in AdmissionGuardrailsService.MODES:
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

    @staticmethod
    def _persist_assessment(
        *,
        db: Session,
        admission: Any,
        tenant_id: str,
        user_id: str,
        patient_id: str,
        status: str,
        severity: str,
        flags: List[str],
        requires_md_review: bool,
    ) -> None:
        assessment = DocumentationAssessment(
            tenant_id=tenant_id,
            patient_id=patient_id,
            admission_id=(
                admission.get("id")
                if isinstance(admission, dict)
                else getattr(admission, "id", None)
            ),
            status=status,
            severity=severity,
            flags=flags,
            requires_md_review=requires_md_review,
            assessed_by=user_id,
            assessed_at=datetime.utcnow(),
        )
        db.add(assessment)

    @staticmethod
    def _audit(
        *,
        db: Session,
        action: str,
        entity_type: str,
        entity_id: str,
        tenant_id: str,
        user_id: str,
        details: Dict[str, Any],
    ) -> None:
        log = AuditLog(
            tenant_id=tenant_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            performed_by=user_id,
            details=details,
            performed_at=datetime.utcnow(),
        )
        db.add(log)