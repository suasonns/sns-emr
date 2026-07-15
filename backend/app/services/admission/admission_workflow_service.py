from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.patient import Patient
from app.services.admission.admission_service import AdmissionService
from app.services.admission.admission_status_history_service import (
    AdmissionStatusHistoryService,
)
from app.services.admission.admission_task_generation_service import (
    AdmissionTaskGenerationService,
)

class AdmissionWorkflowService:
    """
    Admission Workflow Service.

    This is the production orchestration layer for admission status changes.

    Responsibilities:
    - Validate role authority.
    - Validate allowed admission status transitions.
    - Validate admission readiness before ADMITTED.
    - Validate transfer requirements before ADMITTED.
    - Update Patient.admission_status.
    - Create AdmissionStatusHistory audit records.
    - Return blockers when admission or transition is blocked.

    API routes should call this service.
    API routes should NOT directly update patient.admission_status.
    """

    @classmethod
    def change_status(
        cls,
        *,
        db: Session,
        patient: Patient,
        new_status: str,
        changed_by: UUID,
        role: str,
        reason: Optional[str] = None,
        notes: Optional[str] = None,
        commit: bool = True,
    ) -> Dict[str, Any]:
        """
        Change a patient's admission status.

        This method is the single production entry point for admission
        status changes.

        Supported examples:

        REFERRAL
            ->
        POTENTIAL_ADMISSION

        POTENTIAL_ADMISSION
            ->
        ADMISSION_SCHEDULED

        ADMISSION_SCHEDULED
            ->
        SOC_IN_PROGRESS

        SOC_IN_PROGRESS
            ->
        ADMITTED

        Any allowed admission status
            ->
        NON_ADMIT

        If the transition is invalid or admission blockers exist,
        the patient status is not changed.
        """

        current_status = patient.admission_status

        validation_result = AdmissionService.validate_status_change(
            patient=patient,
            current_status=current_status,
            target_status=new_status,
            role=role,
        )

        if not validation_result["allowed"]:
            return {
                "success": False,
                "patient_id": str(patient.id),
                "previous_status": current_status,
                "new_status": new_status,
                "status_changed": False,
                "reason": validation_result.get("reason"),
                "blockers": validation_result.get("blockers", []),
            }

        history = AdmissionStatusHistoryService.update_patient_status(
            db=db,
            patient=patient,
            new_status=new_status,
            changed_by=changed_by,
            reason=reason,
            notes=notes,
        )

        task_generation_result = (
            AdmissionTaskGenerationService.generate_transition_tasks(
                db=db,
                patient=patient,
                previous_status=current_status,
                new_status=new_status,
                created_by=changed_by,

                is_medicare=getattr(
                    patient,
                    "is_medicare",
                    False,
                ),

                msw_ordered=getattr(
                    patient,
                    "msw_ordered",
                    False,
                ),

                sc_ordered=getattr(
                    patient,
                    "sc_ordered",
                    False,
                ),

                chha_ordered=getattr(
                    patient,
                    "chha_ordered",
                    False,
                ),
            )
        )

        if commit:
            db.commit()
            db.refresh(patient)
            db.refresh(history)
        else:
            db.flush()

        return {
            "success": True,
            "patient_id": str(patient.id),
            "previous_status": current_status,
            "new_status": new_status,
            "status_changed": True,
            "history_id": str(history.id),
            "reason": reason,
            "blockers": [],

            "created_tasks":
                task_generation_result["created_tasks"],

            "created_task_count":
                task_generation_result["created_count"],

            "skipped_existing_tasks":
                task_generation_result[
                    "skipped_existing_tasks"
                ],

            "skipped_condition_tasks":
                task_generation_result[
                    "skipped_condition_tasks"
                ],
            } 

    @classmethod
    def validate_status_change(
        cls,
        *,
        patient: Patient,
        new_status: str,
        role: str,
    ) -> Dict[str, Any]:
        """
        Validate a status change without updating the database.

        Useful for:
        - Previewing blockers.
        - Dashboard readiness checks.
        - UI validation before submit.
        """

        return AdmissionService.validate_status_change(
            patient=patient,
            current_status=patient.admission_status,
            target_status=new_status,
            role=role,
        )

    @classmethod
    def get_admission_summary(
        cls,
        *,
        patient: Patient,
    ) -> Dict[str, Any]:
        """
        Return dashboard-friendly admission readiness summary.
        """

        result = AdmissionService.get_admission_summary(
            patient=patient,
        )

        return {
            "patient_id": str(patient.id),
            "admission_status": patient.admission_status,
            "ready_for_soc": result["ready_for_soc"],
            "blocker_count": result["blocker_count"],
            "blockers": result["blockers"],
        }

    @classmethod
    def mark_non_admit(
        cls,
        *,
        db: Session,
        patient: Patient,
        changed_by: UUID,
        role: str,
        reason: str,
        notes: Optional[str] = None,
        commit: bool = True,
    ) -> Dict[str, Any]:
        """
        Mark a patient as NON_ADMIT.

        This preserves the admission workflow audit trail.
        """

        return cls.change_status(
            db=db,
            patient=patient,
            new_status="NON_ADMIT",
            changed_by=changed_by,
            role=role,
            reason=reason,
            notes=notes,
            commit=commit,
        )

    @classmethod
    def start_soc(
        cls,
        *,
        db: Session,
        patient: Patient,
        changed_by: UUID,
        role: str,
        reason: Optional[str] = "SOC visit started",
        notes: Optional[str] = None,
        commit: bool = True,
    ) -> Dict[str, Any]:
        """
        Move patient into SOC_IN_PROGRESS.

        This does not admit the patient.

        ADMITTED only occurs after SOC Date/Time is entered
        and admission readiness passes.
        """

        return cls.change_status(
            db=db,
            patient=patient,
            new_status="SOC_IN_PROGRESS",
            changed_by=changed_by,
            role=role,
            reason=reason,
            notes=notes,
            commit=commit,
        )

    @classmethod
    def complete_admission(
        cls,
        *,
        db: Session,
        patient: Patient,
        changed_by: UUID,
        role: str,
        reason: Optional[str] = "SOC completed",
        notes: Optional[str] = None,
        commit: bool = True,
    ) -> Dict[str, Any]:
        """
        Move patient into ADMITTED.

        This enforces:
        - Admission readiness gate
        - Transfer validation
        - Role authority
        - Allowed transition path
        """

        return cls.change_status(
            db=db,
            patient=patient,
            new_status="ADMITTED",
            changed_by=changed_by,
            role=role,
            reason=reason,
            notes=notes,
            commit=commit,
        )