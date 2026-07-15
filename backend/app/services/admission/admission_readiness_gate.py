from typing import Dict, List

from app.services.admission.transfer_validation_service import (
    TransferValidationService,
)

class AdmissionReadinessGate:

    @staticmethod
    def evaluate(patient) -> Dict:

        blockers: List[str] = []

        if not patient.primary_diagnosis:
            blockers.append(
                "Primary diagnosis not established"
            )

        if not patient.primary_payer:
            blockers.append(
                "Primary payer not selected"
            )

        if not patient.admission_order_present:
            blockers.append(
                "Hospice admission order missing"
            )

        if not patient.rn_assigned:
            blockers.append(
                "Admitting RN not assigned"
            )

        if not patient.clinical_evidence_complete:
            blockers.append(
                "Clinical evidence packet incomplete"
            )

        if (
            patient.requires_eligibility
            and
            not patient.eligibility_complete
        ):
            blockers.append(
                "Eligibility incomplete"
            )

        transfer_result = (
            TransferValidationService.evaluate(
                patient
            )
        )

        if not transfer_result["ready"]:
            blockers.extend(
                transfer_result["blockers"]
        )

        return {
            "ready": len(blockers) == 0,
            "blockers": blockers,
        }