from datetime import datetime
from uuid import uuid4
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.plan_of_care import PlanOfCare
from app.models.plan_of_care_version import PlanOfCareVersion


def create_plan_of_care(
    db: Session,
    *,
    patient_id,
    created_by_user_id,
    poc_content: dict
):
    """
    Creates base POC and initial version.

    PRODUCTION RULE:
    - Initial version is PENDING
    - It is NOT considered clinically active
    - current_version_id is allowed ONLY as initial placeholder
    """

    try:
        poc = PlanOfCare(
            id=uuid4(),
            patient_id=patient_id,
            status="ACTIVE",
            created_at=datetime.utcnow(),
            created_by_user_id=created_by_user_id
        )
        db.add(poc)
        db.flush()

        version = PlanOfCareVersion(
            id=uuid4(),
            plan_of_care_id=poc.id,
            version_number=1,
            snapshot_json=poc_content,
            approval_status="PENDING",
            created_at=datetime.utcnow(),
            created_by_user_id=created_by_user_id
        )
        db.add(version)
        db.flush()

        # Initial pointer (NOT clinically enforced)
        poc.current_version_id = version.id

        db.commit()
        return poc

    except Exception:
        db.rollback()
        raise


def create_new_version(
    db: Session,
    *,
    plan_of_care: PlanOfCare,
    updated_content: dict,
    user_id
):
    """
    Creates a NEW PENDING version.

    CRITICAL:
    - DOES NOT activate version
    - DOES NOT change current_version_id
    """

    try:
        current_version = (
            db.query(PlanOfCareVersion)
            .filter(PlanOfCareVersion.plan_of_care_id == plan_of_care.id)
            .order_by(desc(PlanOfCareVersion.version_number))
            .first()
        )

        if not current_version:
            raise ValueError("Current version not found")

        new_version = PlanOfCareVersion(
            id=uuid4(),
            plan_of_care_id=plan_of_care.id,
            version_number=current_version.version_number + 1,
            based_on_version_id=current_version.id,
            snapshot_json=updated_content,
            approval_status="PENDING",
            created_at=datetime.utcnow(),
            created_by_user_id=user_id
        )

        db.add(new_version)
        db.commit()

        return new_version

    except Exception:
        db.rollback()
        raise


def get_active_plan_of_care(
    db: Session,
    *,
    plan_of_care_id
):
    poc = db.query(PlanOfCare).get(plan_of_care_id)
    if not poc:
        return None

    return (
        db.query(PlanOfCareVersion)
        .filter(
            PlanOfCareVersion.plan_of_care_id == poc.id,
            PlanOfCareVersion.id == poc.current_version_id
        )
        .first()
    )
    if approved_version:
        return approved_version

    # fallback (safe behavior)
    latest_version = (
        db.query(PlanOfCareVersion)
        .filter(PlanOfCareVersion.plan_of_care_id == poc.id)
        .order_by(desc(PlanOfCareVersion.version_number))
        .first()
    )

    return latest_version


def approve_plan_of_care_version(
    db: Session,
    *,
    version_id,
    approved_by_user_id
):
    """
    Approves version AND makes it ACTIVE.

    CRITICAL:
    - Approval controls activation
    """

    try:
        version = db.query(PlanOfCareVersion).get(version_id)
        if not version:
            raise ValueError("Version not found")

        if version.approval_status == "APPROVED":
            return version

        version.approval_status = "APPROVED"
        version.approved_at = datetime.utcnow()
        version.approved_by_user_id = approved_by_user_id

        plan_of_care = (
            db.query(PlanOfCare)
            .filter(PlanOfCare.id == version.plan_of_care_id)
            .first()
        )

        if not plan_of_care:
            raise ValueError("Plan of Care not found")

        # ✅ ONLY PLACE THAT SETS ACTIVE VERSION
        plan_of_care.current_version_id = version.id

        db.commit()
        return version

    except Exception:
        db.rollback()
        raise