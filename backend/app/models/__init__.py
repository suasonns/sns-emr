"""
RESTORE MODE: Minimal SQLAlchemy model import surface.

Purpose:
- Allow staged ORM restoration
- Avoid circular imports
- Prevent FK resolution explosions
- Keep DB and rules inert
"""

# ---------------------------------------------------------
# Foundation
# ---------------------------------------------------------
from app.models.tenant import Tenant
from app.models.user import User
from app.models.role import Role
from app.models.interface import Interface

# ---------------------------------------------------------
# Patient core
# ---------------------------------------------------------
import app.models.patient as _patient
import app.models.visit as _visit
import app.models.benefit_period as _benefit_period

Patient = _patient.Patient
Visit = _visit.Visit
BenefitPeriod = _benefit_period.BenefitPeriod

# ---------------------------------------------------------
# IDG / Documentation
# ---------------------------------------------------------
import app.models.idg_review as _idg_review
import app.models.idg_note as _idg_note
import app.models.idg_signature as _idg_signature
import app.models.idg_md_attestation as _idg_md_attestation

import app.models.document_record as _document_record
import app.models.document_notification as _document_notification
import app.models.document_idg_resolution as _document_idg_resolution

from .assessment import Assessment
from .assessment_reference import AssessmentReference
from .assessment_discrepancy import AssessmentDiscrepancy

IDGReview = _idg_review.IDGReview
IDGNote = _idg_note.IDGNote
IDGSignature = _idg_signature.IDGSignature
IDGMDAttestation = _idg_md_attestation.IDGMDAttestation

DocumentRecord = _document_record.DocumentRecord
DocumentNotification = _document_notification.DocumentNotification
DocumentIDGResolution = _document_idg_resolution.DocumentIDGResolution

# ---------------------------------------------------------
# Tasks / Access
# ---------------------------------------------------------
import app.models.task as _task
import app.models.survey_access as _survey_access

Task = _task.Task
SurveyAccess = _survey_access.SurveyAccess

# ---------------------------------------------------------
# Rule‑related models (INERT)
# ---------------------------------------------------------
import app.models.dx_primary_policy as _dx_primary_policy
import app.models.drug_alias as _drug_alias
import app.models.eligibility as _eligibility
import app.models.eligibility_decision as _eligibility_decision

DxPrimaryPolicy = _dx_primary_policy.DxPrimaryPolicy
DrugAlias = _drug_alias.DrugAlias

EligibilityAssessment = _eligibility.EligibilityAssessment
EligibilityRuleset = _eligibility.EligibilityRuleset

EligibilityDecision = _eligibility_decision.EligibilityDecision