from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.admission_status_history import (
    AdmissionStatusHistory,
)
from app.models.patient import Patient


class AdmissionStatusHistoryService:
    """
    Admission Status History Service

    Responsibilities:
    - Create admission status audit records
    - Track all admission workflow movements
    - Preserve survey-ready audit history
    - Prevent duplicate transition records
    """

    @staticmethod
    def record_transition(
        *,
        db: Session,
        patient: Patient,
        previous_status: str,
        new_status: str,
        changed_by: UUID,
        reason: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> AdmissionStatusHistory:
        """
        Create admission status history record.

        Example:

        REFERRAL
            ->
        POTENTIAL_ADMISSION

        ADMISSION_SCHEDULED
            ->
        SOC_IN_PROGRESS

        SOC_IN_PROGRESS
            ->
        ADMITTED
        """

        history = AdmissionStatusHistory(
            tenant_id=patient.tenant_id,
            patient_id=patient.id,
            previous_status=previous_status,
            new_status=new_status,
            changed_by=changed_by,
            reason=reason,
            notes=notes,
        )

        db.add(history)

        return history

    @staticmethod
    def update_patient_status(
        *,
        db: Session,
        patient: Patient,
        new_status: str,
        changed_by: UUID,
        reason: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> AdmissionStatusHistory:
        """
        Update patient admission status
        and automatically create history record.
        """

        previous_status = patient.admission_status

        history = AdmissionStatusHistoryService.record_transition(
            db=db,
            patient=patient,
            previous_status=previous_status,
            new_status=new_status,
            changed_by=changed_by,
            reason=reason,
            notes=notes,
        )

        patient.admission_status = new_status

        return history

    @staticmethod
    def get_latest_status(
        *,
        patient: Patient,
    ) -> Optional[str]:
        """
        Return current admission status.
        """

        return patient.admission_status

    @staticmethod
    def get_status_history(
        *,
        db: Session,
        patient_id: UUID,
    ):
        """
        Returns complete admission history
        oldest -> newest.
        """

        return (
            db.query(AdmissionStatusHistory)
            .filter(
                AdmissionStatusHistory.patient_id
                == patient_id
            )
            .order_by(
                AdmissionStatusHistory.changed_at.asc()
            )
            .all()
        )

    @staticmethod
    def get_latest_transition(
        *,
        db: Session,
        patient_id: UUID,
    ) -> Optional[AdmissionStatusHistory]:
        """
        Returns most recent status transition.
        """

        return (
            db.query(AdmissionStatusHistory)
            .filter(
                AdmissionStatusHistory.patient_id
                == patient_id
            )
            .order_by(
                AdmissionStatusHistory.changed_at.desc()
            )
            .first()
        )

    @staticmethod
    def has_transition(
        *,
        db: Session,
        patient_id: UUID,
        previous_status: str,
        new_status: str,
    ) -> bool:
        """
        Utility method used for testing,
        audit verification,
        and duplicate prevention.
        """

        existing = (
            db.query(AdmissionStatusHistory)
            .filter(
                AdmissionStatusHistory.patient_id
                == patient_id,
                AdmissionStatusHistory.previous_status
                == previous_status,
                AdmissionStatusHistory.new_status
                == new_status,
            )
            .first()
        )

        return existing is not None