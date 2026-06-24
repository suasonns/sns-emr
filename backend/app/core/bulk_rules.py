# app/core/bulk_rules.py

def is_bulk_action(
    *,
    document_count: int = 0,
    patient_count: int | None = None,
) -> bool:
    return (
        document_count >= 10
        or (patient_count is not None and patient_count >= 5)
    )
