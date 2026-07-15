from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.patient import Patient

from app.models.plan_of_care import PlanOfCare
from app.models.plan_of_care_version import PlanOfCareVersion

from app.models.poc_physician_approval import (
    PocPhysicianApproval,
    PocPhysicianApprovalAuditEvent,
)


PHYSICIAN_ATTESTATION_TEXT = """
I have reviewed the patient's clinical status,
hospice eligibility information, current problems,
goals, interventions, medications, and the Plan of Care.

I certify that the Plan of Care is appropriate for
the patient's current condition and hospice needs.

I approve this Plan of Care and authorize its
continued implementation and ongoing interdisciplinary
management.

Electronic signature or submission of a signed
approval document constitutes physician attestation
and approval of this Plan of Care version.
""".strip()


APPROVAL_RECORD_CREATED_EVENT_TYPE = "APPROVAL_RECORD_CREATED"


APPROVAL_RECORD_CREATED_DESCRIPTION = (
    "Physician approval record automatically created for Plan of Care version."
)


def create_plan_of_care(
    db: Session,
    *,
    tenant_id,
    patient_id,
    created_by_user_id,
    poc_content: dict,
):
    try:
        now = datetime.now(timezone.utc)

        patient = (
            db.query(Patient)
            .filter(
                Patient.id == patient_id,
                Patient.tenant_id == tenant_id,
            )
            .first()
        )

        if not patient:
            raise ValueError("Patient not found in tenant")

        poc = PlanOfCare(
            id=uuid4(),
            tenant_id=tenant_id,
            patient_id=patient_id,
            status="DRAFT",
            created_at=now,
            created_by_user_id=created_by_user_id,
        )

        db.add(poc)
        db.flush()

        version = PlanOfCareVersion(
            id=uuid4(),
            plan_of_care_id=poc.id,
            version_number=1,
            snapshot_json=poc_content,
            approval_status="PENDING",
            created_at=now,
            created_by_user_id=created_by_user_id,
        )

        db.add(version)
        db.flush()

        approval = PocPhysicianApproval(
            tenant_id=tenant_id,
            patient_id=patient_id,
            poc_version_id=version.id,
            physician_name="PENDING",
            physician_role="ATTENDING_PHYSICIAN",
            approval_method="ELECTRONIC_SIGNATURE",
            approval_status="PENDING_PHYSICIAN_SIGNATURE",
            attestation_text=PHYSICIAN_ATTESTATION_TEXT,
            created_by_user_id=created_by_user_id,
        )

        db.add(approval)
        db.flush()

        audit = PocPhysicianApprovalAuditEvent(
            tenant_id=tenant_id,
            poc_physician_approval_id=approval.id,
            patient_id=patient_id,
            poc_version_id=version.id,
            event_type=APPROVAL_RECORD_CREATED_EVENT_TYPE,
            event_description=APPROVAL_RECORD_CREATED_DESCRIPTION,
            performed_by_user_id=created_by_user_id,
        )

        db.add(audit)
        db.flush()

        poc.current_version_id = version.id

        db.commit()
        db.refresh(poc)

        return poc

    except Exception:
        db.rollback()
        raise


def create_new_version(
    db: Session,
    *,
    plan_of_care: PlanOfCare,
    updated_content: dict,
    user_id,
):
    try:
        now = datetime.now(timezone.utc)

        current_version = (
            db.query(PlanOfCareVersion)
            .filter(PlanOfCareVersion.plan_of_care_id == plan_of_care.id)
            .order_by(desc(PlanOfCareVersion.version_number))
            .with_for_update()
            .first()
        )

        if not current_version:
            raise ValueError("Current version not found")

        tenant_id = plan_of_care.tenant_id
        patient_id = plan_of_care.patient_id

        patient = (
            db.query(Patient)
            .filter(
                Patient.id == patient_id,
                Patient.tenant_id == tenant_id,
            )
            .first()
        )

        if not patient:
            raise ValueError("Patient not found in tenant")

        new_version = PlanOfCareVersion(
            id=uuid4(),
            plan_of_care_id=plan_of_care.id,
            version_number=current_version.version_number + 1,
            based_on_version_id=current_version.id,
            snapshot_json=updated_content,
            approval_status="PENDING",
            created_at=now,
            created_by_user_id=user_id,
        )

        db.add(new_version)
        db.flush()

        approval = PocPhysicianApproval(
            tenant_id=tenant_id,
            patient_id=patient_id,
            poc_version_id=new_version.id,
            physician_name="PENDING",
            physician_role="ATTENDING_PHYSICIAN",
            approval_method="ELECTRONIC_SIGNATURE",
            approval_status="PENDING_PHYSICIAN_SIGNATURE",
            attestation_text=PHYSICIAN_ATTESTATION_TEXT,
            created_by_user_id=user_id,
        )

        db.add(approval)
        db.flush()

        audit = PocPhysicianApprovalAuditEvent(
            tenant_id=tenant_id,
            poc_physician_approval_id=approval.id,
            patient_id=patient_id,
            poc_version_id=new_version.id,
            event_type=APPROVAL_RECORD_CREATED_EVENT_TYPE,
            event_description=APPROVAL_RECORD_CREATED_DESCRIPTION,
            performed_by_user_id=user_id,
        )

        db.add(audit)
        db.flush()

        db.commit()
        db.refresh(new_version)

        return new_version

    except Exception:
        db.rollback()
        raise


def get_active_plan_of_care(
    db: Session,
    *,
    plan_of_care_id,
):
    poc = db.get(PlanOfCare, plan_of_care_id)

    if not poc:
        return None

    version = db.get(PlanOfCareVersion, poc.current_version_id)

    if version:
        return version

    return (
        db.query(PlanOfCareVersion)
        .filter(PlanOfCareVersion.plan_of_care_id == poc.id)
        .order_by(desc(PlanOfCareVersion.version_number))
        .first()
    )


def approve_plan_of_care_version(
    db: Session,
    *,
    version_id,
    approved_by_user_id,
):
    try:
        now = datetime.now(timezone.utc)

        version = db.get(PlanOfCareVersion, version_id)

        if not version:
            raise ValueError("Version not found")

        latest_version = (
            db.query(PlanOfCareVersion)
            .filter(PlanOfCareVersion.plan_of_care_id == version.plan_of_care_id)
            .order_by(desc(PlanOfCareVersion.version_number))
            .first()
        )

        if not latest_version:
            raise ValueError("Latest version not found")

        if version.id != latest_version.id:
            raise ValueError("Cannot approve non-latest version")

        if version.approval_status == "APPROVED":
            return version

        plan_of_care = db.get(PlanOfCare, version.plan_of_care_id)

        if not plan_of_care:
            raise ValueError("Plan of Care not found")

        version.approval_status = "APPROVED"
        version.approved_at = now
        version.approved_by_user_id = approved_by_user_id

        plan_of_care.current_version_id = version.id
        plan_of_care.status = "ACTIVE"

        db.commit()
        db.refresh(version)

        return version

    except Exception:
        db.rollback()
        raise