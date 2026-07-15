from enum import Enum
from typing import Any, Dict, List


class AdmissionStatus(str, Enum):
    REFERRAL = "REFERRAL"
    POTENTIAL_ADMISSION = "POTENTIAL_ADMISSION"
    ADMISSION_SCHEDULED = "ADMISSION_SCHEDULED"
    TRANSFER_PENDING = "TRANSFER_PENDING"
    SOC_IN_PROGRESS = "SOC_IN_PROGRESS"
    ADMITTED = "ADMITTED"
    NON_ADMIT = "NON_ADMIT"


class AdmissionStatusEngine:

    ALLOWED_TRANSITIONS = {
        AdmissionStatus.REFERRAL: [
            AdmissionStatus.POTENTIAL_ADMISSION,
            AdmissionStatus.NON_ADMIT,
        ],

        AdmissionStatus.POTENTIAL_ADMISSION: [
            AdmissionStatus.ADMISSION_SCHEDULED,
            AdmissionStatus.TRANSFER_PENDING,
            AdmissionStatus.NON_ADMIT,
        ],

        AdmissionStatus.ADMISSION_SCHEDULED: [
            AdmissionStatus.SOC_IN_PROGRESS,
            AdmissionStatus.TRANSFER_PENDING,
            AdmissionStatus.NON_ADMIT,
        ],

        AdmissionStatus.TRANSFER_PENDING: [
            AdmissionStatus.ADMISSION_SCHEDULED,
            AdmissionStatus.SOC_IN_PROGRESS,
            AdmissionStatus.NON_ADMIT,
        ],

        AdmissionStatus.SOC_IN_PROGRESS: [
            AdmissionStatus.ADMITTED,
            AdmissionStatus.NON_ADMIT,
        ],

        AdmissionStatus.ADMITTED: [],

        AdmissionStatus.NON_ADMIT: [],
    }

    AUTHORIZED_ROLES = {
        "ADMIN",
        "CASE_MANAGER",
        "DPCS",
        "DPCS_DESIGNEE",
        "ASSIGNED_RN",
        "MEDICAL_DIRECTOR",
        "MEDICAL_DIRECTOR_DESIGNEE",
        "ASSOCIATE_MEDICAL_DIRECTOR",
    }

    @classmethod
    def can_transition(
        cls,
        current_status: str,
        target_status: str,
    ) -> bool:
        current = AdmissionStatus(current_status)
        target = AdmissionStatus(target_status)

        return target in cls.ALLOWED_TRANSITIONS.get(
            current,
            [],
        )

    @classmethod
    def role_can_change_status(
        cls,
        role: str,
    ) -> bool:
        return role in cls.AUTHORIZED_ROLES

    @classmethod
    def validate_transition(
        cls,
        current_status: str,
        target_status: str,
        role: str,
    ) -> Dict[str, Any]:

        if not cls.role_can_change_status(role):
            return {
                "allowed": False,
                "reason": (
                    f"Role '{role}' is not authorized."
                ),
            }

        if not cls.can_transition(
            current_status,
            target_status,
        ):
            return {
                "allowed": False,
                "reason": (
                    f"Invalid transition "
                    f"{current_status} -> "
                    f"{target_status}"
                ),
            }

        return {
            "allowed": True,
            "reason": None,
        }

    @classmethod
    def get_visible_tasks(
        cls,
        status: str,
    ) -> List[str]:

        status = AdmissionStatus(status)

        if status == AdmissionStatus.REFERRAL:
            return [
                "REFERRAL_INTAKE",
                "DEMOGRAPHICS_COLLECTION",
                "CONTACT_COLLECTION",
                "INSURANCE_ENTRY",
                "CLINICAL_RECORD_REQUEST",
                "HNP_REQUEST",
            ]

        if status == AdmissionStatus.POTENTIAL_ADMISSION:
            return [
                "ELIGIBILITY_REVIEW",
                "INSURANCE_REVIEW",
                "CLINICAL_EVIDENCE_COLLECTION",
                "ADMISSION_ORDER_COLLECTION",
                "PRIMARY_DIAGNOSIS_VALIDATION",
                "FAMILY_CONTACT",
            ]

        if status == AdmissionStatus.ADMISSION_SCHEDULED:
            return [
                "ADMISSION_SCHEDULING",
                "DME_COORDINATION",
                "MEDICATION_COORDINATION",
                "TRANSPORTATION_COORDINATION",
                "CONSENT_PREPARATION",
                "ELIGIBILITY_COMPLETION",
            ]

        if status == AdmissionStatus.TRANSFER_PENDING:
            return [
                "TRANSFER_REVIEW",
                "TRANSFER_ELIGIBILITY_REVIEW",
                "BENEFIT_PERIOD_VERIFICATION",
                "DAYS_USED_VERIFICATION",
                "DAYS_REMAINING_VERIFICATION",
                "TRANSFER_CTI_COLLECTION",
                "TRANSFER_ORDER_COLLECTION",
            ]

        if status == AdmissionStatus.SOC_IN_PROGRESS:
            return [
                "RN_ADMISSION_ASSESSMENT",
                "CONSENT_COMPLETION",
                "PRIMARY_DIAGNOSIS_CONFIRMATION",
                "ORDER_VALIDATION",
                "MEDICATION_RECONCILIATION",
                "CAREGIVER_EDUCATION",
            ]

        if status == AdmissionStatus.ADMITTED:
            return [
                "RN_ICA",
                "POC_WORKFLOW",
                "CTI_WORKFLOW",
                "MEDICATION_REVIEW",
                "VISIT_FREQUENCIES",
                "CARE_PLAN_TASKS",
                "ADMISSION_COMPLIANCE_TASKS",
            ]

        if status == AdmissionStatus.NON_ADMIT:
            return [
                "NON_ADMIT_DOCUMENTATION",
                "NON_ADMIT_REASON",
                "REFERRAL_CLOSURE",
            ]

        return []

    @classmethod
    def get_hidden_tasks(
        cls,
        status: str,
    ) -> List[str]:

        status = AdmissionStatus(status)

        if status in {
            AdmissionStatus.REFERRAL,
            AdmissionStatus.POTENTIAL_ADMISSION,
            AdmissionStatus.ADMISSION_SCHEDULED,
            AdmissionStatus.TRANSFER_PENDING,
        }:
            return [
                "RN_ICA",
                "POC_WORKFLOW",
                "CTI_WORKFLOW",
                "MSW_ICA",
                "SC_ICA",
                "CHHA_TASKS",
                "NOE_WORKFLOW",
                "RECERTIFICATION",
                "IDG_REVIEW",
            ]

        return []