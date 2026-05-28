"""
RESTORE MODE: Minimal SQLAlchemy model import surface.

Purpose:
- Allow staged ORM restoration
- Avoid circular imports
- Prevent FK resolution explosions
- Keep DB and rule engines inert

IMPORTANT:
- This module exists ONLY to force model registration on Base.metadata
- Alembic relies on the SIDE EFFECTS of these imports
"""

from __future__ import annotations

# ---------------------------------------------------------
# Foundation (must load first)
# ---------------------------------------------------------
from app.models.tenant import Tenant  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.role import Role  # noqa: F401
from app.models.interface import Interface  # noqa: F401

# ---------------------------------------------------------
# Patient core
# ---------------------------------------------------------
import app.models.patient  # noqa: F401
import app.models.visit  # noqa: F401
import app.models.benefit_period  # noqa: F401

# ---------------------------------------------------------
# IDG / Documentation (FK ROOT MUST LOAD FIRST)
# ---------------------------------------------------------
import app.models.idg_meeting  # noqa: F401  ✅ REQUIRED FK ROOT

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
# Tasks / Access
# ---------------------------------------------------------
import app.models.task  # noqa: F401
import app.models.survey_access  # noqa: F401

# ---------------------------------------------------------
# Rule-related models (INERT — imported only for metadata)
# ---------------------------------------------------------
import app.models.dx_primary_policy  # noqa: F401
import app.models.drug_alias  # noqa: F401
import app.models.eligibility  # noqa: F401
import app.models.eligibility_decision  # noqa: F401