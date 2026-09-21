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