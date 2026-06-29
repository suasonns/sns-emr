from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
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
    Enterprise Hospice Admission Guardrails (Policy-Driven)

    Goals:
    - deterministic decision support
    - runtime-safe imports
    - no hardcoded regulatory thresholds
    - audit traceability
    - safe fallback behavior when optional policy/model layers do not exist
    """

    SERVICE_VERSION = "v3.0"

    LCD_BAD = {"INCOMPLETE", "INCONSISTENT", "NARRATIVE_REQUIRED"}
    SEVERITY_ORDER = ["INFO", "WARNING", "HIGH", "CRITICAL"]
    MODES = {"OFF", "SILENT", "GUIDANCE", "STRICT"}

    # =====================================================
    # POLICY ENGINE (dynamic, no hardcoding)
    # =====================================================

    @staticmethod
    def _get_policy(db: Session, tenant_id: str, key: str, default: Any):
        """
        Resolve a guardrail policy value dynamically.

        Safe fallback behavior:
        - if GuardrailPolicy model/table is not implemented yet, return default
        - if query fails for any reason, return default
        """
        try:
            from app.models.guardrail_policy import GuardrailPolicy  # lazy import

            value = (
                db.query(GuardrailPolicy.value)
                .filter(
                    GuardrailPolicy.tenant_id == tenant_id,
                    GuardrailPolicy.policy_key == key,
                )
                .scalar()
            )

            return value if value is not None else default

        except Exception:
            return default

    # =====================================================
    # MAIN ENTRY
    # =====================================================

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

        flush=False -> decision support only (no DB side effects)
        flush=True  -> audit log persistence
        """
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

        now = datetime.now(timezone.utc)
        correlation_id = str(uuid.uuid4())

        mode = AdmissionGuardrailsService._get_guardrail_mode(db, tenant_id)

        narrative = (narrative_text or "").strip()
        flags: List[str] = []
        severity = "INFO"
        requires_md_review = False

        # =================================================
        # Dynamic policies
        # =================================================
        min_narrative_length = AdmissionGuardrailsService._get_policy(
            db,
            tenant_id,
            "MIN_NARRATIVE_LENGTH",
            200,
        )

        require_decline = AdmissionGuardrailsService._get_policy(
            db,
            tenant_id,
            "REQUIRE_MEASURABLE_DECLINE",
            True,
        )

        # =================================================
        # Narrative validation
        # =================================================
        if not narrative:
            flags.append("MISSING_ELIGIBILITY_NARRATIVE")
            severity = AdmissionGuardrailsService._escalate(severity, "HIGH")
        elif len(narrative) < int(min_narrative_length):
            flags.append("WEAK_ELIGIBILITY_NARRATIVE")
            severity = AdmissionGuardrailsService._escalate(severity, "WARNING")

        # =================================================
        # Decline validation
        # =================================================
        if require_decline and not has_measurable_decline:
            flags.append("NO_MEASURABLE_EVIDENCE_OF_DECLINE")
            severity = AdmissionGuardrailsService._escalate(severity, "HIGH")

        # =================================================
        # LCD / documentation consistency check
        # =================================================
        if lcd_status:
            lcd_code = str(lcd_status).strip().upper()
            if lcd_code in AdmissionGuardrailsService.LCD_BAD:
                flags.append(f"LCD_STATUS_{lcd_code}")
                severity = AdmissionGuardrailsService._escalate(severity, "CRITICAL")

        if severity == "CRITICAL":
            requires_md_review = True

        hard_stop = (mode == "STRICT" and severity in {"HIGH", "CRITICAL"})
        status = AdmissionGuardrailsService._map_status(severity)

        result = {
            "status": status,
            "severity": severity,
            "flags": flags,
            "requires_md_review": requires_md_review,
            "hard_stop": hard_stop,
            "rn_explanation": RN_DOCUMENTATION_GUIDANCE,
            "guardrail_mode": mode,
            "service_version": AdmissionGuardrailsService.SERVICE_VERSION,
        }

        # =================================================
        # Audit persistence
        # =================================================
        if mode != "OFF" and flush:
            try:
                AdmissionGuardrailsService._audit(
                    db=db,
                    action="ADMISSION_RISK_ASSESSMENT",
                    entity_type="ADMISSION",
                    entity_id=str(
                        admission.get("id")
                        if isinstance(admission, dict)
                        else getattr(admission, "id", "")
                    ),
                    tenant_id=tenant_id,
                    user_id=user_id,
                    correlation_id=correlation_id,
                    details=result,
                    now=now,
                )
                db.flush()
            except Exception:
                db.rollback()
                raise

        return result

    # =====================================================
    # HELPERS
    # =====================================================

    @staticmethod
    def _get_guardrail_mode(db: Session, tenant_id: str) -> str:
        """
        Resolve guardrail mode from optional tenant settings service.
        Safe fallback to GUIDANCE if the service is not present.
        """
        try:
            from app.services.tenant_settings_service import TenantSettingsService  # lazy import

            mode = TenantSettingsService.get_guardrail_mode(db, tenant_id)
            if isinstance(mode, str):
                normalized = mode.strip().upper()
                if normalized in AdmissionGuardrailsService.MODES:
                    return normalized
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
    def _audit(
        *,
        db: Session,
        action: str,
        entity_type: str,
        entity_id: str,
        tenant_id: str,
        user_id: str,
        correlation_id: str,
        details: Dict[str, Any],
        now: datetime,
    ) -> None:
        log = AuditLog(
            tenant_id=tenant_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            performed_by=user_id,
            correlation_id=correlation_id,
            details=details,
            performed_at=now,
        )
        db.add(log)