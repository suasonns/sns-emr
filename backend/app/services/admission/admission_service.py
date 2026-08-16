"""
Admission Service

Master orchestration layer for admissions.

Responsibilities:
- Validate status transitions
- Validate admission readiness
- Validate transfer requirements
- Determine admission eligibility
- Provide consolidated blockers
"""

from typing import Any, Dict
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.admission import Admission
from app.services.admission.admission_readiness_gate import (
    AdmissionReadinessGate,
)
from app.services.admission.admission_status_engine import (
    AdmissionStatus,
    AdmissionStatusEngine,
)
from app.services.admission.transfer_validation_service import (
    TransferValidationService,
)


class AdmissionService:

    @classmethod
    def get_latest_admission(
        cls,
        *,
        db: Session,
        patient_id: UUID,
        tenant_id: UUID | None = None,
    ) -> Admission | None:
        """
        Most recent admission for a patient. Callers treat None as missing.
        """
        query = db.query(Admission).filter(Admission.patient_id == patient_id)

        if tenant_id is not None:
            query = query.filter(Admission.tenant_id == tenant_id)

        return query.order_by(Admission.created_at.desc()).first()

    @classmethod
    def validate_status_change(
        cls,
        *,
        patient: Any,
        current_status: str,
        target_status: str,
        role: str,
    ) -> Dict:
        """
        Validate status transition.

        Checks:
        1. User role
        2. Allowed transition path
        3. Admission hard-stop rules (if applicable)
        """

        transition_result = (
            AdmissionStatusEngine.validate_transition(
                current_status=current_status,
                target_status=target_status,
                role=role,
            )
        )

        if not transition_result["allowed"]:
            return transition_result

        if target_status == AdmissionStatus.ADMITTED:

            admission_result = cls.can_admit(
                patient=patient,
            )

            if not admission_result["allowed"]:
                return admission_result

        return {
            "allowed": True,
            "reason": None,
            "blockers": [],
        }

    @classmethod
    def can_admit(
        cls,
        *,
        patient: Any,
    ) -> Dict:
        """
        Master admission validation.

        Admission is allowed only if:
        - Readiness Gate passes
        - Transfer Validation passes
        """

        blockers = []

        readiness_result = (
            AdmissionReadinessGate.evaluate(
                patient
            )
        )

        blockers.extend(
            readiness_result["blockers"]
        )

        transfer_result = (
            TransferValidationService.evaluate(
                patient
            )
        )

        blockers.extend(
            transfer_result["blockers"]
        )

        return {
            "allowed": len(blockers) == 0,
            "blockers": blockers,
        }

    @classmethod
    def get_admission_blockers(
        cls,
        *,
        patient: Any,
    ) -> Dict:
        """
        Convenience method.

        Returns all current blockers without
        attempting status transition.
        """

        result = cls.can_admit(
            patient=patient,
        )

        return {
            "ready": result["allowed"],
            "blockers": result["blockers"],
        }

    @classmethod
    def is_ready_for_soc(
        cls,
        *,
        patient: Any,
    ) -> bool:

        result = cls.can_admit(
            patient=patient,
        )

        return result["allowed"]

    @classmethod
    def get_admission_summary(
        cls,
        *,
        patient: Any,
    ) -> Dict:
        """
        Dashboard-friendly summary.
        """

        result = cls.can_admit(
            patient=patient,
        )

        return {
            "ready_for_soc": result["allowed"],
            "blocker_count": len(
                result["blockers"]
            ),
            "blockers": result["blockers"],
        }