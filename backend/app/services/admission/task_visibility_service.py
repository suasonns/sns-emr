"""
Admission Task Visibility Service.

This service controls which tasks should be visible or hidden
based on the patient's admission status.

Purpose:
- Prevent premature active-patient alerts.
- Prevent RN ICA / POC / CTI / NOE tasks from appearing before SOC.
- Keep admission workflow aligned with real hospice operations.
"""

from enum import Enum
from typing import List


class AdmissionStatus(str, Enum):
    REFERRAL = "REFERRAL"
    POTENTIAL_ADMISSION = "POTENTIAL_ADMISSION"
    ADMISSION_SCHEDULED = "ADMISSION_SCHEDULED"
    TRANSFER_PENDING = "TRANSFER_PENDING"
    SOC_IN_PROGRESS = "SOC_IN_PROGRESS"
    ADMITTED = "ADMITTED"
    NON_ADMIT = "NON_ADMIT"


class AdmissionTaskVisibilityService:
    """
    Determines which tasks are visible or hidden
    for each admission status.
    """

    # ---------------------------------------------------------
    # Universal active hospice tasks
    # ---------------------------------------------------------
    ACTIVE_HOSPICE_TASKS = [
        "RN_ICA",
        "POC_WORKFLOW",
        "CTI_WORKFLOW",
        "MSW_ICA",
        "SC_ICA",
        "CHHA_TASKS",
        "NOE_WORKFLOW",
        "RECERTIFICATION",
        "IDG_REVIEW",
        "VISIT_FREQUENCY_COMPLIANCE",
        "BEREAVEMENT_WORKFLOW",
    ]

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------
    @classmethod
    def get_visible_tasks(
        cls,
        admission_status: str,
        *,
        is_transfer: bool = False,
        is_medicare: bool = False,
        msw_ordered: bool = False,
        sc_ordered: bool = False,
        chha_ordered: bool = False,
    ) -> List:
        """
        Return tasks visible for the current admission status.
        """

        status = cls._normalize_status(admission_status)

        if status == AdmissionStatus.REFERRAL:
            return cls._referral_tasks()

        if status == AdmissionStatus.POTENTIAL_ADMISSION:
            return cls._potential_admission_tasks(
                is_transfer=is_transfer,
            )

        if status == AdmissionStatus.ADMISSION_SCHEDULED:
            return cls._admission_scheduled_tasks(
                is_transfer=is_transfer,
            )

        if status == AdmissionStatus.TRANSFER_PENDING:
            return cls._transfer_pending_tasks()

        if status == AdmissionStatus.SOC_IN_PROGRESS:
            return cls._soc_in_progress_tasks()

        if status == AdmissionStatus.ADMITTED:
            return cls._admitted_tasks(
                is_medicare=is_medicare,
                msw_ordered=msw_ordered,
                sc_ordered=sc_ordered,
                chha_ordered=chha_ordered,
            )

        if status == AdmissionStatus.NON_ADMIT:
            return cls._non_admit_tasks()

        return []

    @classmethod
    def get_hidden_tasks(
        cls,
        admission_status: str,
        *,
        is_transfer: bool = False,
        is_medicare: bool = False,
        msw_ordered: bool = False,
        sc_ordered: bool = False,
        chha_ordered: bool = False,
    ) -> List[str]:
        """
        Return tasks that must remain hidden for the current status.
        """

        visible_tasks = set(
            cls.get_visible_tasks(
                admission_status,
                is_transfer=is_transfer,
                is_medicare=is_medicare,
                msw_ordered=msw_ordered,
                sc_ordered=sc_ordered,
                chha_ordered=chha_ordered,
            )
        )

        return [
            task
            for task in cls.ACTIVE_HOSPICE_TASKS
            if task not in visible_tasks
        ]

    @classmethod
    def is_task_visible(
        cls,
        admission_status: str,
        task_type: str,
        *,
        is_transfer: bool = False,
        is_medicare: bool = False,
        msw_ordered: bool = False,
        sc_ordered: bool = False,
        chha_ordered: bool = False,
    ) -> bool:
        """
        Return True if a task should be visible for the current status.
        """

        visible_tasks = cls.get_visible_tasks(
            admission_status,
            is_transfer=is_transfer,
            is_medicare=is_medicare,
            msw_ordered=msw_ordered,
            sc_ordered=sc_ordered,
            chha_ordered=chha_ordered,
        )

        return task_type in visible_tasks

    @classmethod
    def is_task_hidden(
        cls,
        admission_status: str,
        task_type: str,
        *,
        is_transfer: bool = False,
        is_medicare: bool = False,
        msw_ordered: bool = False,
        sc_ordered: bool = False,
        chha_ordered: bool = False,
    ) -> bool:
        """
        Return True if a task should remain hidden for the current status.
        """

        return not cls.is_task_visible(
            admission_status,
            task_type,
            is_transfer=is_transfer,
            is_medicare=is_medicare,
            msw_ordered=msw_ordered,
            sc_ordered=sc_ordered,
            chha_ordered=chha_ordered,
        )

    # ---------------------------------------------------------
    # Status task definitions
    # ---------------------------------------------------------
    @staticmethod
    def _referral_tasks() -> List[str]:
        return [
            "REFERRAL_INTAKE",
            "DEMOGRAPHICS_COLLECTION",
            "CONTACT_COLLECTION",
            "INSURANCE_ENTRY",
            "CLINICAL_RECORD_REQUEST",
            "HNP_REQUEST",
            "PRIMARY_CONTACT_COLLECTION",
        ]

    @staticmethod
    def _potential_admission_tasks(
        *,
        is_transfer: bool,
    ) -> List[str]:
        tasks = [
            "ELIGIBILITY_REVIEW",
            "INSURANCE_REVIEW",
            "ELIGIBILITY_DOCUMENT_UPLOAD",
            "CLINICAL_EVIDENCE_COLLECTION",
            "ADMISSION_ORDER_COLLECTION",
            "PRIMARY_DIAGNOSIS_VALIDATION",
            "FAMILY_CONTACT",
            "RN_ASSIGNMENT",
        ]

        if is_transfer:
            tasks.extend(
                [
                    "TRANSFER_REVIEW",
                    "TRANSFER_FORM_UPLOAD",
                    "TRANSFER_ELIGIBILITY_REVIEW",
                    "BENEFIT_PERIOD_VERIFICATION",
                    "DAYS_USED_VERIFICATION",
                    "DAYS_REMAINING_VERIFICATION",
                ]
            )

        return tasks

    @staticmethod
    def _admission_scheduled_tasks(
        *,
        is_transfer: bool,
    ) -> List[str]:
        tasks = [
            "ADMISSION_SCHEDULING",
            "DME_COORDINATION",
            "MEDICATION_COORDINATION",
            "TRANSPORTATION_COORDINATION",
            "CONSENT_PREPARATION",
            "ADMISSION_BINDER_PREPARATION",
            "ELIGIBILITY_COMPLETION",
            "CLINICAL_EVIDENCE_FINAL_REVIEW",
            "ADMISSION_ORDER_FINAL_REVIEW",
        ]

        if is_transfer:
            tasks.extend(
                [
                    "TRANSFER_EFFECTIVE_DATE_MONITORING",
                    "TRANSFER_CTI_COLLECTION",
                    "TRANSFER_ORDER_COLLECTION",
                    "TRANSFER_PACKET_FINAL_REVIEW",
                ]
            )

        return tasks

    @staticmethod
    def _transfer_pending_tasks() -> List[str]:
        return [
            "TRANSFER_FORM_REVIEW",
            "TRANSFER_ELIGIBILITY_REVIEW",
            "BENEFIT_PERIOD_VERIFICATION",
            "DAYS_USED_VERIFICATION",
            "DAYS_REMAINING_VERIFICATION",
            "CURRENT_CERTIFICATION_PERIOD_VERIFICATION",
            "SENDING_HOSPICE_VERIFICATION",
            "TRANSFER_EFFECTIVE_DATE_MONITORING",
            "TRANSFER_CTI_COLLECTION",
            "TRANSFER_ORDER_COLLECTION",
        ]

    @staticmethod
    def _soc_in_progress_tasks() -> List[str]:
        return [
            "RN_ADMISSION_ASSESSMENT",
            "CONSENT_COMPLETION",
            "PRIMARY_DIAGNOSIS_CONFIRMATION",
            "ORDER_VALIDATION",
            "MEDICATION_RECONCILIATION",
            "CAREGIVER_EDUCATION",
            "ADMISSION_DOCUMENT_COLLECTION",
            "SOC_DATE_TIME_ENTRY",
        ]

    @staticmethod
    def _admitted_tasks(
        *,
        is_medicare: bool,
        msw_ordered: bool,
        sc_ordered: bool,
        chha_ordered: bool,
    ) -> List[str]:
        tasks = [
            "RN_ICA",
            "POC_WORKFLOW",
            "CTI_WORKFLOW",
            "MEDICATION_REVIEW",
            "ORDER_MANAGEMENT",
            "VISIT_FREQUENCIES",
            "CARE_PLAN_TASKS",
            "ADMISSION_COMPLIANCE_TASKS",
            "BEREAVEMENT_CONTACT_VERIFICATION",
            "PATIENT_NOTIFICATION_TRACKING",
        ]

        if msw_ordered:
            tasks.extend(
                [
                    "MSW_ICA",
                    "MSW_VISIT_TASKS",
                ]
            )

        if sc_ordered:
            tasks.extend(
                [
                    "SC_ICA",
                    "SC_VISIT_TASKS",
                ]
            )

        if chha_ordered:
            tasks.extend(
                [
                    "CHHA_TASKS",
                    "CHHA_POC",
                    "CHHA_VISIT_DOCUMENTATION",
                    "CHHA_FREQUENCY_TASKS",
                ]
            )

        if is_medicare:
            tasks.append("NOE_WORKFLOW")

        if not msw_ordered and not sc_ordered:
            tasks.append("RN_BEREAVEMENT_REVIEW_REQUIRED")

        return tasks

    @staticmethod
    def _non_admit_tasks() -> List[str]:
        return [
            "NON_ADMIT_DOCUMENTATION",
            "NON_ADMIT_REASON",
            "REFERRAL_CLOSURE",
            "RECORD_RETENTION",
        ]

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------
    @staticmethod
    def _normalize_status(
        admission_status: str,
    ) -> AdmissionStatus:
        try:
            return AdmissionStatus(admission_status)
        except ValueError:
            raise ValueError(
                f"Invalid admission status: {admission_status}"
            )