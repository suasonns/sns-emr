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
# PATIENT CORE
# ---------------------------------------------------------

import app.models.patient  # noqa: F401
import app.models.visit  # noqa: F401
import app.models.benefit_period  # noqa: F401

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

# ✅ NEW — STEP 7 AUDIT LOG (REQUIRED)
import app.billing.models.claim_export_log  # noqa: F401
