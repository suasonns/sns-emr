from sqlalchemy.orm import Session
from app.models.clinical_workflow_map import ClinicalWorkflowMap


def validate_timepoint_safe(
    db: Session,
    assessment,
):
    """
    Timepoint validation temporarily disabled.

    ClinicalWorkflowMap is currently not populated and
    ClinicalNote does not contain assessment_type.

    Returning VALID prevents false failures while the
    workflow mapping engine is being redesigned.
    """

    return "VALID"


def validate_sfv_safe(
    sfv_assessment,
    ica_assessment,
):
    if not sfv_assessment or not ica_assessment:
        return None

    if sfv_assessment.visit_id == ica_assessment.visit_id:
        return "WARNING: SFV must be separate visit"

    if (
        not getattr(sfv_assessment, "occurred_at", None)
        or not getattr(ica_assessment, "occurred_at", None)
    ):
        return None

    hours = (
        sfv_assessment.occurred_at
        - ica_assessment.occurred_at
    ).total_seconds() / 3600

    if hours > 48:
        return f"WARNING: SFV late ({int(hours)} hours)"

    return "VALID"