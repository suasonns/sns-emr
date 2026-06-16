class ClaimValidationError(Exception):
    pass


def validate_claim(export_payload: dict):
    """
    Returns:
        {
            "errors": [...],
            "warnings": [...]
        }
    """

    errors = []
    warnings = []

    claim_header = export_payload.get("claim_header", {})
    patient = export_payload.get("patient", {})
    claim_lines = export_payload.get("claim_lines", [])

    if not patient.get("patient_id"):
        errors.append("Missing patient ID")

    if not claim_header.get("statement_from_date"):
        errors.append("Missing statement_from_date")

    if not claim_lines:
        errors.append("No claim lines")

    for line in claim_lines:
        if not line.get("revenue_code"):
            errors.append("Missing revenue_code")

        amount = float(line.get("estimated_amount", 0))
        if amount == 0:
            warnings.append("Zero billing amount detected")

    return {
        "errors": errors,
        "warnings": warnings
    }