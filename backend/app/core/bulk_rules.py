# app/core/bulk_rules.py

def is_bulk_action(
    *,
    document_count: int = 0,
    patient_count: int | None = None,
) -> bool:
    """
    Defines what constitutes a 'bulk' action requiring step-up authentication.

    Rules:
    - More than 1 document = bulk
    - More than 1 patient = bulk
    """

    if document_count > 1:
        return True

    if patient_count is not None and patient_count > 1:
        return True

    return False