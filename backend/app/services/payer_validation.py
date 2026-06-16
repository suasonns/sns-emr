from __future__ import annotations


class PayerValidationError(RuntimeError):
    pass


def validate_payer_for_claim(insurance: dict) -> None:
    """
    ✅ ENTERPRISE VALIDATION — PREVENTS INVALID CLAIMS

    This MUST run before:
    - EDI generation
    - billing submission

    Raises:
        PayerValidationError if validation fails
    """

    payer_type = insurance.get("payer_type")
    subscriber_id = insurance.get("subscriber_id")
    subscriber_id_type = insurance.get("subscriber_id_type")

    # ---------------------------------------------------------
    # ✅ MEDICARE RULE (CRITICAL)
    # ---------------------------------------------------------
    if payer_type == "MEDICARE":

        if not subscriber_id:
            raise PayerValidationError(
                "Missing MBI (subscriber_id) for Medicare claim"
            )

        if subscriber_id_type != "MBI":
            raise PayerValidationError(
                f"Invalid subscriber_id_type '{subscriber_id_type}' "
                f"for Medicare. Expected 'MBI'"
            )

    # ---------------------------------------------------------
    # ✅ GENERIC RULE (ALL PAYERS)
    # ---------------------------------------------------------
    if not subscriber_id:
        raise PayerValidationError(
            f"Missing subscriber_id for payer {payer_type}"
        )
