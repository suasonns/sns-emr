from sqlalchemy.orm import Session
from app.models.clinical_workflow_map import ClinicalWorkflowMap


def resolve_workflow(
    db: Session,
    discipline: str,
    assessment_type: str,
    visit_type: str | None = None,
):
    """
    Resolve workflow mapping from database.

    Returns:
        ClinicalWorkflowMap row containing form_type and rules
    """

    query = db.query(ClinicalWorkflowMap).filter(
        ClinicalWorkflowMap.discipline == discipline,
        ClinicalWorkflowMap.assessment_type == assessment_type
    )

    result = query.first()

    if not result:
        raise ValueError(
            f"No workflow mapping found for {discipline} / {assessment_type}"
        )

    return result