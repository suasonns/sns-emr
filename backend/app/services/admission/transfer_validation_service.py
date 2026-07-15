from typing import Dict, List


class TransferValidationService:

    @staticmethod
    def evaluate(patient) -> Dict:

        blockers: List[str] = []

        if not patient.is_transfer:
            return {
                "ready": True,
                "blockers": [],
            }

        if not patient.transfer_form_uploaded:
            blockers.append(
                "Transfer form missing"
            )

        if not patient.transfer_eligibility_complete:
            blockers.append(
                "Transfer eligibility incomplete"
            )

        if not patient.benefit_period_verified:
            blockers.append(
                "Benefit period not verified"
            )

        if not patient.days_used_verified:
            blockers.append(
                "Days used not verified"
            )

        if not patient.days_remaining_verified:
            blockers.append(
                "Days remaining not verified"
            )

        if not patient.transfer_effective_date:
            blockers.append(
                "Transfer effective date missing"
            )

        if not patient.transfer_orders_present:
            blockers.append(
                "Transfer orders missing"
            )

        if not patient.transfer_cti_present:
            blockers.append(
                "Transfer CTI missing"
            )

        return {
            "ready": len(blockers) == 0,
            "blockers": blockers,
        }