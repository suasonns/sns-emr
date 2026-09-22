from __future__ import annotations

"""
Shared helpers for the Clinical Outcome / IDG Follow-Up / Election
Compliance-Review API layer (issue #143/#145 API phase).

Every mutating endpoint in this layer MUST resolve tenant_id and actor
identity/discipline through these helpers -- never from a client-supplied
payload field. See app.services.clinical_outcome_service and
app.services.idg_follow_up_service module docstrings for why discipline
must come only from the authenticated account.
"""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.permissions import require_roles
from app.dependencies.auth import CurrentUser
from app.models.admission import Admission
from app.models.patient import Patient
from app.models.user import User

# ---------------------------------------------------------------------
# Centralized authorization for this API layer.
#
# Every router in this layer gates access through exactly one of the
# require_*_role() factories below (applied at APIRouter(dependencies=[...])
# level, not scattered per-endpoint role checks). All three build on the
# existing app.core.permissions.require_roles() dependency used by other
# clinical routers (e.g. app/api/idg/router.py, app/api/compliance.py) so
# authorization decoding/enforcement stays in one place repository-wide.
# ---------------------------------------------------------------------

# Mirrors app.api.idg.router.CLINICAL_ROLES -- clinical outcome tracking is
# populated/read by the same disciplines that do IDG follow-up work.
CLINICAL_OUTCOME_ROLES = ["LVN", "RN", "NP", "PA", "MD", "SW", "CHAPLAIN", "ADMINISTRATOR", "DPCS"]

# Mirrors app.api.idg.router.IDG_VIEW_ROLES (CLINICAL_ROLES + ADMIN_ROLES) --
# this domain literally extends the existing idg_reviews table.
IDG_FOLLOW_UP_ROLES = ["LVN", "RN", "NP", "PA", "MD", "SW", "CHAPLAIN", "ADMINISTRATOR", "DPCS"]

# Mirrors app.api.compliance.py's role set for the sibling compliance domain;
# resolving an election-addendum date review is a compliance/administrative
# determination, so QA/compliance-officer roles are included alongside the
# clinical roles who may originate the underlying election record.
COMPLIANCE_REVIEW_ROLES = [
    "RN",
    "NP",
    "MD",
    "SW",
    "ADMINISTRATOR",
    "DPCS",
    "DPCS_ADMINISTRATOR",
    "COMPLIANCE_OFFICER",
    "QA_MANAGER",
    "QA_REVIEWER",
]


def require_clinical_outcome_role():
    return require_roles(CLINICAL_OUTCOME_ROLES)


def require_idg_follow_up_role():
    return require_roles(IDG_FOLLOW_UP_ROLES)


def require_compliance_review_role():
    return require_roles(COMPLIANCE_REVIEW_ROLES)


# Mirrors COMPLIANCE_REVIEW_ROLES -- the item-level relatedness-review
# workflow is performed by the same clinical/compliance disciplines that
# resolve the underlying election-date compliance review.
ELECTION_ADDENDUM_WORKFLOW_ROLES = [
    "RN",
    "NP",
    "MD",
    "SW",
    "ADMINISTRATOR",
    "DPCS",
    "DPCS_ADMINISTRATOR",
    "COMPLIANCE_OFFICER",
    "QA_MANAGER",
    "QA_REVIEWER",
]


def require_election_addendum_workflow_role():
    return require_roles(ELECTION_ADDENDUM_WORKFLOW_ROLES)


def resolve_actor(db: Session, current_user: CurrentUser) -> tuple[str, str | None]:
    """
    Returns (actor_user_id, actor_account_discipline) resolved strictly
    from the authenticated account row -- never from request payloads.
    """
    user = db.get(User, current_user.id)
    if user is None or not getattr(user, "active", True):
        raise HTTPException(status_code=401, detail="Authenticated user not found or inactive")
    discipline = user.discipline or user.role
    return current_user.id, discipline


def get_tenant_patient(db: Session, tenant_id: str, patient_id: str) -> Patient:
    patient = db.get(Patient, patient_id)
    if patient is None or str(patient.tenant_id) != str(tenant_id):
        # Deliberately identical 404 whether the record doesn't exist or
        # belongs to another tenant -- never disclose cross-tenant existence.
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


def get_tenant_admission(db: Session, tenant_id: str, admission_id: str, *, patient_id: str | None = None) -> Admission:
    admission = db.get(Admission, admission_id)
    if admission is None or str(admission.tenant_id) != str(tenant_id):
        raise HTTPException(status_code=404, detail="Admission not found")
    if patient_id is not None and str(admission.patient_id) != str(patient_id):
        raise HTTPException(status_code=404, detail="Admission not found")
    return admission
