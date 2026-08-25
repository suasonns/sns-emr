"""
MODEL REGISTRY (ENTERPRISE SAFE)

Purpose:
- Forces registration of ALL ORM models into Base.metadata
- Required for Alembic autogeneration
- Guarantees relationship resolution at runtime

RULES:
- DO NOT REMOVE IMPORTS
- DO NOT ADD BUSINESS LOGIC
- USE ONLY DIRECT CLASS IMPORTS
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
# ✅ PATIENT DOMAIN
# ---------------------------------------------------------

from app.models.patient import Patient
from app.models.patient_assignment import PatientAssignment
from app.models.patient_payer import PatientPayer
from app.models.patient_insurance import PatientInsurance
from app.models.patient_facesheet import PatientFaceSheet
from app.models.patient_diagnosis import PatientDiagnosis
from app.models.physician import Physician, PhysicianPecosCache
from app.models.vendor import Vendor
from app.models.visit import Visit
from app.models.benefit_period import BenefitPeriod

from app.models.medication import Medication
from app.models.patient_allergy import PatientAllergy
from app.models.patient_issue import PatientIssue
from app.models.admission import Admission
from app.models.referral import Referral
from app.models.bereavement_assessment import BereavementAssessment
from app.models.bereavement_poc import BereavementPOC
from app.models.post_death_bereavement_assessment import PostDeathBereavementAssessment
from app.models.bereavement_letter_tracker import BereavementLetterTracker
from app.models.bereavement_communication_note import BereavementCommunicationNote
from app.models.patient_evidence import PatientEvidenceRecord, PatientHarvestedSignal

# ---------------------------------------------------------
# ✅ CLINICAL DOMAIN
# ---------------------------------------------------------

from app.models.clinical_note import ClinicalNote
from app.models.notification import Notification
from app.models.rn_recert_assessment import RNRecertAssessment
from app.models.rnica_assessment import RnicaAssessment
from app.models.admission_action_request import AdmissionActionRequest
from app.models.rnica_amendment import RnicaAmendment
from app.models.msw_ica_assessment import MswIcaAssessment
from app.models.scica_assessment import ScicaAssessment
from app.models.communications_log import CommunicationsLog

# ---------------------------------------------------------
# ✅ CHHA DOMAIN
# ---------------------------------------------------------

from app.models.chha_visit_outcome import CHHAVisitOutcome
from app.models.chha_visit_task_result import CHHAVisitTaskResult

# ---------------------------------------------------------
# ✅ CONTINUOUS CARE (shared hourly narrative form)
# ---------------------------------------------------------

from app.models.cc_hourly_narrative_entry import CCHourlyNarrativeEntry

# ---------------------------------------------------------
# ✅ PATIENT SUPPORT / DEPENDENCIES
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
from app.models.idg_group import IDGGroup
from app.models.idg_group_schedule_rule import IDGGroupScheduleRule
from app.models.idg_review import IDGReview
from app.models.idg_note import IDGNote
from app.models.idg_signature import IDGSignature
from app.models.idg_md_attestation import IDGMDAttestation
from app.models.idg_meeting_patient_review import IDGMeetingPatientReview
from app.models.idg_attendee import IDGAttendee
from app.models.idg_justification import IDGJustification
from app.models.dx_primary_policy import DxPrimaryPolicy
from app.models.eligibility_decision import EligibilityDecision
from app.models.diagnosis_source import DiagnosisSource
from app.models.security_activity_event import SecurityActivityEvent

from app.models.document_record import DocumentRecord
from app.models.idg_intelligence_item import IDGIntelligenceItem
from app.models.idg_priority_rule import IDGPriorityRule
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
# HOSPITALIZATION PREVENTION / FAMILY RISK
# ---------------------------------------------------------

from app.models.hospitalization_prevention import (
    FamilyConcernCategory,
    FamilyConcernItem,
    FamilyConcernCluster,
    FamilyRiskAssessment,
    FamilyEducationTask,
    TeachBackRecord,
    DiseaseProcessAlignmentReview,
    DiseaseProcessInterventionReview,
    MedicationReconciliationReview,
    BehavioralEscalationReview,
    HospitalizationPreventionSummary,
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
# ✅ BILLING
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
from app.billing.models.claim_export_log import ClaimExportLog
from app.billing.models.claim_edi_batch import ClaimEdiBatch
from app.billing.models.claim import Claim
from app.billing.models.remittance_advice import RemittanceAdvice
from app.billing.models.payment import Payment
from app.billing.models.payment_adjustment import PaymentAdjustment
from app.billing.models.denial import Denial
from app.billing.models.appeal import Appeal
from app.billing.models.payer_eligibility_check import PayerEligibilityCheck
from app.billing.models.hospice_cap_record import HospiceCapRecord
from app.billing.models.noe_edi_submission import NoeEdiSubmission
from app.billing.models.election_addendum_request import ElectionAddendumRequest

# ---------------------------------------------------------
# ✅ POC PHYSICIAN APPROVAL TRACKING
# ---------------------------------------------------------

from app.models.poc_physician_approval import (
    PocPhysicianApproval,
    PocPhysicianApprovalDocument,
    PocPhysicianApprovalAuditEvent,
)

# ---------------------------------------------------------
# ✅ PHYSICIAN IDENTITY / ORDERS PHASE 1 / CTI / F2F / SIGNATURE AUTHORITY
# ---------------------------------------------------------

from app.models.patient_physician_assignment import PatientPhysicianAssignment
from app.models.patient_contact import PatientContact
from app.models.patient_code_status import PatientCodeStatus
from app.models.physician_order import PhysicianOrder, PhysicianOrderStatusEvent
from app.models.certification import Certification, CertificationStatusEvent
from app.models.f2f_encounter import F2FEncounter, F2FEncounterStatusEvent

# ---------------------------------------------------------
# ✅ EXPORT (REQUIRED)
# ---------------------------------------------------------

__all__ = ["Base"]