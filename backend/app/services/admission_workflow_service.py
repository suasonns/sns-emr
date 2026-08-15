from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.admission import Admission
from app.models.patient import Patient
from app.services.admission_status_history_writer import (
    write_admission_status_history,
)


class AdmissionWorkflowService:
    """
    Admission workflow service with automatic status audit logging.

    This service is designed to be used by the existing API routes that call:
      - get_admission_summary
      - change_status
      - start_soc
      - complete_admission
      - mark_non_admit

    Every status change writes one AdmissionStatusHistory row in the same DB transaction.
    """

    # ---------------------------------------------------------
    # INTERNAL HELPERS
    # ---------------------------------------------------------

    @staticmethod
    def _utc_now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _to_naive_utc(dt: datetime) -> datetime:
        """
        Convert timezone-aware datetime to naive UTC for DB columns that are
        timestamp without time zone.
        """
        if dt.tzinfo is None:
            return dt
        return dt.astimezone(timezone.utc).replace(tzinfo=None)

    @staticmethod
    def _get_latest_admission(
        db: Session,
        *,
        patient_id,
        tenant_id,
    ) -> Admission | None:
        return (
            db.query(Admission)
            .filter(
                Admission.patient_id == patient_id,
                Admission.tenant_id == tenant_id,
            )
            .order_by(Admission.created_at.desc())
            .first()
        )

    @classmethod
    def _require_latest_admission(
        cls,
        db: Session,
        *,
        patient: Patient,
    ) -> Admission:
        admission = cls._get_latest_admission(
            db,
            patient_id=patient.id,
            tenant_id=patient.tenant_id,
        )
        if not admission:
            raise ValueError("Admission record missing")
        return admission

    @classmethod
    def _validate_soc_start(
        cls,
        *,
        admission: Admission,
    ) -> None:
        if admission.discharged_at is not None:
            raise ValueError("Cannot start SOC after discharge")

        if admission.soc_date is not None:
            raise ValueError("SOC already recorded for this admission")

    @classmethod
    def _validate_admission_completion(
        cls,
        *,
        admission: Admission,
    ) -> None:
        if admission.soc_date is None:
            raise ValueError("SOC must be completed before admission")

        if admission.discharged_at is not None:
            raise ValueError("Cannot complete admission after discharge")

    @classmethod
    def _record_status_change(
        cls,
        db: Session,
        *,
        patient: Patient,
        admission: Admission,
        changed_by,
        previous_status: str | None,
        new_status: str,
        reason: str | None = None,
        notes: str | None = None,
        changed_at: datetime | None = None,
    ) -> None:
        write_admission_status_history(
            db,
            tenant_id=patient.tenant_id,
            patient_id=patient.id,
            admission_id=admission.id,
            previous_status=previous_status,
            new_status=new_status,
            changed_by=changed_by,
            changed_at=changed_at,
            reason=reason,
            notes=notes,
            flush=True,
        )

    @classmethod
    def _apply_status_transition(
        cls,
        db: Session,
        *,
        patient: Patient,
        admission: Admission,
        new_status: str,
        changed_by,
        reason: str | None = None,
        notes: str | None = None,
        changed_at: datetime | None = None,
        allow_noop: bool = False,
    ) -> dict[str, Any]:
        if not new_status or not str(new_status).strip():
            raise ValueError("new_status is required")

        event_time = changed_at or cls._utc_now()
        previous_status = admission.status
        normalized_status = str(new_status).strip()

        if previous_status == normalized_status and not allow_noop:
            return {
                "success": True,
                "changed": False,
                "patient_id": str(patient.id),
                "admission_id": str(admission.id),
                "previous_status": previous_status,
                "new_status": normalized_status,
                "message": "No status change",
            }

        # Update admission row
        admission.status = normalized_status
        admission.updated_at = cls._to_naive_utc(event_time)
        admission.updated_by = changed_by

        # Workflow-specific timestamp side effects
        if normalized_status == "ADMITTED":
            if admission.admission_date is None:
                admission.admission_date = cls._to_naive_utc(event_time)

        if normalized_status == "DISCHARGED":
            if admission.discharged_at is None:
                admission.discharged_at = event_time

        # Write audit history
        cls._record_status_change(
            db,
            patient=patient,
            admission=admission,
            changed_by=changed_by,
            previous_status=previous_status,
            new_status=normalized_status,
            reason=reason,
            notes=notes,
            changed_at=event_time,
        )

        db.flush()

        return {
            "success": True,
            "changed": True,
            "patient_id": str(patient.id),
            "admission_id": str(admission.id),
            "previous_status": previous_status,
            "new_status": normalized_status,
            "changed_at": event_time,
        }

    # ---------------------------------------------------------
    # PUBLIC METHODS USED BY ROUTES
    # ---------------------------------------------------------

    @classmethod
    def get_admission_summary(
        cls,
        *,
        db: Session,
        patient: Patient,
    ) -> dict[str, Any]:
        admission = cls._get_latest_admission(
            db,
            patient_id=patient.id,
            tenant_id=patient.tenant_id,
        )

        if not admission:
            return {
                "success": True,
                "patient_id": str(patient.id),
                "has_admission": False,
                "admission": None,
            }

        return {
            "success": True,
            "patient_id": str(patient.id),
            "has_admission": True,
            "admission": {
                "id": str(admission.id),
                "tenant_id": str(admission.tenant_id),
                "patient_id": str(admission.patient_id),
                "status": admission.status,
                "admission_date": admission.admission_date,
                "soc_date": admission.soc_date,
                "soc_time": admission.soc_time,
                "effective_date": admission.effective_date,
                "election_signed_at": admission.election_signed_at,
                "certification_completed_at": admission.certification_completed_at,
                "physician_order_signed_at": admission.physician_order_signed_at,
                "initial_assessment_completed_at": admission.initial_assessment_completed_at,
                "admission_authorized_at": admission.admission_authorized_at,
                "admission_authorized_by": (
                    str(admission.admission_authorized_by)
                    if admission.admission_authorized_by
                    else None
                ),
                "referral_source": admission.referral_source,
                "reason_for_admission": admission.reason_for_admission,
                "discharged_at": admission.discharged_at,
                "discharge_reason": admission.discharge_reason,
                "created_at": admission.created_at,
                "created_by": str(admission.created_by),
                "updated_at": admission.updated_at,
                "updated_by": (
                    str(admission.updated_by)
                    if admission.updated_by
                    else None
                ),
            },
        }

    @classmethod
    def change_status(
        cls,
        *,
        db: Session,
        patient: Patient,
        new_status: str,
        changed_by,
        role: str | None = None,
        reason: str | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        admission = cls._require_latest_admission(
            db,
            patient=patient,
        )

        return cls._apply_status_transition(
            db,
            patient=patient,
            admission=admission,
            new_status=new_status,
            changed_by=changed_by,
            reason=reason,
            notes=notes,
        )

    @classmethod
    def start_soc(
        cls,
        *,
        db: Session,
        patient: Patient,
        changed_by,
        role: str | None = None,
        notes: str | None = None,
        soc_datetime: datetime | None = None,
    ) -> dict[str, Any]:
        admission = cls._require_latest_admission(
            db,
            patient=patient,
        )

        cls._validate_soc_start(admission=admission)

        event_time = soc_datetime or cls._utc_now()

        # Store SOC on admission episode
        admission.soc_date = cls._to_naive_utc(event_time)
        admission.soc_time = cls._to_naive_utc(event_time)

        if admission.effective_date is None:
            admission.effective_date = event_time

        return cls._apply_status_transition(
            db,
            patient=patient,
            admission=admission,
            new_status="SOC_IN_PROGRESS",
            changed_by=changed_by,
            reason="SOC start",
            notes=notes,
            changed_at=event_time,
        )

    @classmethod
    def complete_admission(
        cls,
        *,
        db: Session,
        patient: Patient,
        changed_by,
        role: str | None = None,
        notes: str | None = None,
        admit_datetime: datetime | None = None,
    ) -> dict[str, Any]:
        admission = cls._require_latest_admission(
            db,
            patient=patient,
        )

        cls._validate_admission_completion(admission=admission)

        event_time = admit_datetime or cls._utc_now()

        if admission.admission_date is None:
            admission.admission_date = cls._to_naive_utc(event_time)

        if admission.effective_date is None:
            admission.effective_date = event_time

        return cls._apply_status_transition(
            db,
            patient=patient,
            admission=admission,
            new_status="ADMITTED",
            changed_by=changed_by,
            reason="Admission completed",
            notes=notes,
            changed_at=event_time,
        )

    @classmethod
    def mark_non_admit(
        cls,
        *,
        db: Session,
        patient: Patient,
        changed_by,
        role: str | None = None,
        reason: str | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        admission = cls._require_latest_admission(
            db,
            patient=patient,
        )

        return cls._apply_status_transition(
            db,
            patient=patient,
            admission=admission,
            new_status="NON_ADMIT",
            changed_by=changed_by,
            reason=reason or "Marked as non-admit",
            notes=notes,
        )