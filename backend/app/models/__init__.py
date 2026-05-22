# ---------------------------------------------------------
# Core tenant + user models
# ---------------------------------------------------------
from app.models.tenant import Tenant  # noqa: F401
from app.models.user import User  # noqa: F401

# ---------------------------------------------------------
# RBAC / Interface models (CRITICAL for FK resolution)
# ---------------------------------------------------------
from app.models.interface import Interface  # noqa: F401
from app.models.role import Role  # noqa: F401
from app.models.survey_access import SurveyAccess  # noqa: F401
from app.models.task import Task  # noqa: F401

# ---------------------------------------------------------
# Clinical core models
# ---------------------------------------------------------
from app.models.patient import Patient  # noqa: F401
from app.models.visit import Visit  # noqa: F401
from app.models.clinical_note import ClinicalNote  # noqa: F401
from app.models.medication import Medication  # noqa: F401
from app.models.amendment import Amendment  # noqa: F401
from app.models.audit_log import AuditLog  # noqa: F401

# ---------------------------------------------------------
# Benefit periods
# ---------------------------------------------------------
from app.models.benefit_period import BenefitPeriod  # noqa: F401

# ---------------------------------------------------------
# Canonical IDG models (CMS CoPs 418.56)
# ---------------------------------------------------------
from app.models.idg import IDGReview  # noqa: F401
from app.models.idg_signature import IDGSignature  # noqa: F401
from app.models.idg_note import IDGNote  # noqa: F401
from app.models.idg_md_attestation import IDGMDAttestation  # noqa: F401

# ---------------------------------------------------------
# Document awareness / IDG resolution models (CRITICAL)
# ---------------------------------------------------------
from app.models.document_notification import DocumentNotification  # noqa: F401
from app.models.document_idg_resolution import DocumentIDGResolution  # noqa: F401
from app.models.document_record import DocumentRecord  # noqa: F401