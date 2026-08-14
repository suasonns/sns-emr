"""
MODEL REGISTRY (ENTERPRISE SAFE)

Purpose:
- Forces registration of ALL ORM tables into Base.metadata
- Required for Alembic autogeneration
- Prevents missing tables / DROP TABLE bugs

RULES:
- DO NOT REMOVE IMPORTS
- DO NOT ADD BUSINESS LOGIC HERE
- IMPORT ORDER MATTERS
"""

from __future__ import annotations

# ---------------------------------------------------------
# CORE FOUNDATION
# ---------------------------------------------------------

from app.models.tenant import Tenant  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.role import Role  # noqa: F401
from app.models.interface import Interface  # noqa: F401

# ---------------------------------------------------------
# PATIENT CORE (MUST LOAD BEFORE DEPENDENTS)
# ---------------------------------------------------------

import app.models.patient_assignment  # noqa: F401
import app.models.patient  # noqa: F401
import app.models.patient_payer  # noqa: F401
import app.models.visit  # noqa: F401
import app.models.benefit_period  # noqa: F401

# ---------------------------------------------------------
# CORE CLINICAL / NOTES (EARLY LOAD)
# ---------------------------------------------------------

import app.models.clinical_note  # noqa: F401
import app.models.notification  # noqa: F401
import app.models.rn_recert_assessment  # noqa: F401
import app.models.rnica_assessment  # noqa: F401
import app.models.msw_ica_assessment  # noqa: F401
import app.models.communications_log  # noqa: F401

# ---------------------------------------------------------
# ✅ CHHA OUTCOME LAYER (NEW - SAFE ADD)
# ---------------------------------------------------------

from app.models.chha_visit_outcome import CHHAVisitOutcome  # noqa: F401
from app.models.chha_visit_task_result import CHHAVisitTaskResult  # noqa: F401

# ---------------------------------------------------------
# PATIENT DEPENDENCIES (REQUIRED BY RELATIONSHIPS)
# ---------------------------------------------------------

import app.models.service_coverage_decision  # noqa: F401
import app.models.external_substance  # noqa: F401

# ---------------------------------------------------------
# INCIDENTS / EVENTS (REQUIRED FOR TASK FK RESOLUTION)
# ---------------------------------------------------------

import app.models.incident_report  # noqa: F401

# ---------------------------------------------------------
# IDG / DOCUMENTATION
# ---------------------------------------------------------

import app.models.idg_meeting  # noqa: F401
import app.models.idg_review  # noqa: F401
import app.models.idg_note  # noqa: F401
import app.models.idg_signature  # noqa: F401
import app.models.idg_md_attestation  # noqa: F401

import app.models.document_record  # noqa: F401
import app.models.document_notification  # noqa: F401
import app.models.document_idg_resolution  # noqa: F401

import app.models.assessment  # noqa: F401
import app.models.assessment_reference  # noqa: F401
import app.models.assessment_discrepancy  # noqa: F401
import app.models.med_reconciliation  # noqa: F401

from app.models.form_registry_model import FormRegistryModel
from app.models.form import Form
from app.models.form_module import FormModule
from app.models.form_package_module import FormPackageModule

# ---------------------------------------------------------
# TASKS / ACCESS
# ---------------------------------------------------------

import app.models.task  # noqa: F401
import app.models.survey_access  # noqa: F401

# ---------------------------------------------------------
# RULE ENGINE (INERT)
# ---------------------------------------------------------

import app.models.dx_primary_policy  # noqa: F401
import app.models.drug_alias  # noqa: F401
import app.models.eligibility  # noqa: F401
import app.models.eligibility_decision  # noqa: F401

# ---------------------------------------------------------
# BILLING MODELS (REQUIRED FOR ALEMBIC)
# ---------------------------------------------------------

import app.billing.models.billing_cycle  # noqa: F401
import app.billing.models.billing_summary  # noqa: F401
import app.billing.models.billing_snapshot  # noqa: F401
import app.billing.models.patient_pos  # noqa: F401
import app.billing.models.loc_events  # noqa: F401
import app.billing.models.visit_minutes  # noqa: F401
import app.billing.models.orders_snapshot  # noqa: F401
import app.billing.models.payer  # noqa: F401
import app.billing.models.authorization  # noqa: F401
import app.billing.models.contract  # noqa: F401

# ---------------------------------------------------------
# AUDIT / EXPORT
# ---------------------------------------------------------

import app.billing.models.claim_export_log  # noqa: F401