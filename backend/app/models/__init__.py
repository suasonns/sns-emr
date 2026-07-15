"""
MODEL REGISTRY (ENTERPRISE SAFE)

Purpose:
- Forces registration of ALL ORM models into Base.metadata
- Required for Alembic autogeneration
- Guarantees relationship resolution at runtime

RULES:
- DO NOT REMOVE IMPORTS
- DO NOT ADD BUSINESS LOGIC
- USE ONLY ONE IMPORT STYLE (direct class import)
"""

from __future__ import annotations

# ---------------------------------------------------------
# ✅ LOAD BASE FIRST (CRITICAL)
# ---------------------------------------------------------

from app.db.base import Base


# ---------------------------------------------------------
# ✅ CORE FOUNDATION
# ---------------------------------------------------------

from app.models.tenant import Tenant
from app.models.user import User
from app.models.role import Role
from app.models.interface import Interface


# ---------------------------------------------------------
# ✅ PATIENT DOMAIN (LOAD EARLY)
# ---------------------------------------------------------

from app.models.patient import Patient
from app.models.patient_assignment import PatientAssignment
from app.models.patient_payer import PatientPayer
from app.models.patient_insurance import PatientInsurance
from app.models.visit import Visit
from app.models.benefit_period import BenefitPeriod

from app.models.patient_facesheet import PatientFaceSheet
from app.models.patient_diagnosis import PatientDiagnosis

# 🔴 REQUIRED for your error fix
from app.models.medication import Medication


# ---------------------------------------------------------
# ✅ CLINICAL DOMAIN
# ---------------------------------------------------------

from app.models.clinical_note import ClinicalNote
from app.models.notification import Notification
from app.models.rn_recert_assessment import RNRecertAssessment


# ---------------------------------------------------------
# ✅ CHHA DOMAIN
# ---------------------------------------------------------

from app.models.chha_visit_outcome import CHHAVisitOutcome
from app.models.chha_visit_task_result import CHHAVisitTaskResult


# ---------------------------------------------------------
# ✅ PATIENT DEPENDENCIES
# ---------------------------------------------------------

from app.models.service_coverage_decision import ServiceCoverageDecision
from app.models.external_substance import ExternalSubstance


# ---------------------------------------------------------
# ✅ INCIDENT / EVENTS
# ---------------------------------------------------------

from app.models.incident_report import IncidentReport


# ---------------------------------------------------------
# ✅ IDG / DOCUMENTATION
# ---------------------------------------------------------

from app.models.idg_meeting import IDGMeeting
from app.models.idg_review import IDGReview
from app.models.idg_note import IDGNote
from app.models.idg_signature import IDGSignature
from app.models.idg_md_attestation import IDGMDAttestation

from app.models.document_record import DocumentRecord
from app.models.document_notification import DocumentNotification
from app.models.document_idg_resolution import DocumentIDGResolution

from app.models.assessment import Assessment
from app.models.assessment_reference import AssessmentReference
from app.models.assessment_discrepancy import AssessmentDiscrepancy

from app.models.clinical_workflow_map import ClinicalWorkflowMap
from app.models.med_reconciliation import (
    MedReconciliationImport,
    MedReconciliationItem,
)


# ---------------------------------------------------------
# ✅ FORM ENGINE
# ---------------------------------------------------------

from app.models.form_registry_model import FormRegistryModel
from app.models.form import Form
from app.models.form_module import FormModule
from app.models.form_package_module import FormPackageModule


# ---------------------------------------------------------
# ✅ TASKS / ACCESS
# ---------------------------------------------------------

from app.models.task import Task
from app.models.survey_access import SurveyAccess


# ---------------------------------------------------------
# ✅ BILLING (FIXED: DIRECT IMPORTS ONLY)
# ---------------------------------------------------------

from app.billing.models.billing_cycle import BillingCycle
from app.billing.models.billing_summary import BillingSummary
from app.billing.models.billing_snapshot import BillingSnapshot
from app.billing.models.patient_pos import PatientPOS
from app.billing.models.loc_events import (
    GIPPeriod,
    RespitePeriod,
    ContinuousCareEvent,
)
from app.billing.models.visit_minutes import VisitMinutes
from app.billing.models.orders_snapshot import OrdersSnapshot
from app.models.payer import Payer
from app.billing.models.authorization import Authorization
from app.billing.models.contract import Contract


# ---------------------------------------------------------
# ✅ AUDIT / EXPORT
# ---------------------------------------------------------

from app.billing.models.claim_export_log import ClaimExportLog


# ---------------------------------------------------------
# ✅ POC PHYSICIAN APPROVAL TRACKING
# ---------------------------------------------------------

from app.models.poc_physician_approval import (
    PocPhysicianApproval,
    PocPhysicianApprovalDocument,
    PocPhysicianApprovalAuditEvent,
)

# ---------------------------------------------------------
# ✅ EXPORT
# ---------------------------------------------------------

__all__ = ["Base"]

# ---------------------------------------------------------
# ✅ EXPORT
# ---------------------------------------------------------

__all__ = ["Base"]