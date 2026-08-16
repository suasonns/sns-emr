# tests/services/test_admission_guardrails_determinism.py

# --- TEST-LOCAL STUBS (prevent import-time failures) ---
import sys
import types


# Stub: app.models.documentation_assessment
doc_assessment_mod = types.ModuleType("app.models.documentation_assessment")

class _StubDocumentationAssessment:
    pass

doc_assessment_mod.DocumentationAssessment = _StubDocumentationAssessment
sys.modules["app.models.documentation_assessment"] = doc_assessment_mod


# Stub: app.models.audit_log
audit_log_mod = types.ModuleType("app.models.audit_log")

class _StubAuditLog:
    pass

audit_log_mod.AuditLog = _StubAuditLog
sys.modules["app.models.audit_log"] = audit_log_mod


# Stub: app.services.tenant_settings_service
tenant_settings_mod = types.ModuleType("app.services.tenant_settings_service")

class _StubTenantSettingsService:
    @staticmethod
    def get_guardrail_mode(db, tenant_id):
        # Deterministic default for unit tests
        return "GUIDANCE"

tenant_settings_mod.TenantSettingsService = _StubTenantSettingsService
sys.modules["app.services.tenant_settings_service"] = tenant_settings_mod

# ------------------------------------------------------


from app.services.admission.guardrail_assessment_service import (
    AdmissionGuardrailAssessmentService,
)


class FakeDBSession:
    """
    Minimal DB session used for unit tests.
    The guardrails service only calls db.add(...) and optionally db.flush().
    """

    def __init__(self):
        self.added = []
        self.flushed = False

    def add(self, obj):
        self.added.append(obj)

    def flush(self):
        self.flushed = True


def test_guardrails_are_deterministic():
    """
    GIVEN identical inputs
    WHEN assess_admission is called multiple times
    THEN the decision-support output must be identical.
    """

    db = FakeDBSession()

    admission = {
        "id": "patient-123",
        "patient_id": "patient-123",
        "diagnosis_text": "End-stage CHF",
        "eligibility_narrative": (
            "Patient with end-stage congestive heart failure, "
            "PPS 40%, progressive dyspnea at rest, recurrent hospitalizations."
        ),
        "has_measurable_decline": True,
        "lcd_status": "SUPPORTED",
    }

    common_kwargs = {
        "db": db,
        "admission": admission,
        "user_id": "user-1",
        "tenant_id": "tenant-1",
        "patient_id": "patient-123",
        "flush": False,  # IMPORTANT: do not flush in unit tests
    }

    r1 = AdmissionGuardrailAssessmentService.assess_admission(**common_kwargs)
    r2 = AdmissionGuardrailAssessmentService.assess_admission(**common_kwargs)

    # service_version can be ignored if you ever change it; everything else must match
    def scrub(r):
        return {k: v for k, v in r.items() if k != "service_version"}

    assert scrub(r1) == scrub(r2)


def test_guardrails_deterministic_when_borderline():
    db = FakeDBSession()

    admission = {
        "id": "patient-456",
        "patient_id": "patient-456",
        "diagnosis_text": "Debility",
        "eligibility_narrative": "Declining function over several months.",
        "has_measurable_decline": False,
        "lcd_status": "INCOMPLETE",
    }

    kwargs = {
        "db": db,
        "admission": admission,
        "user_id": "user-1",
        "tenant_id": "tenant-1",
        "patient_id": "patient-456",
        "flush": False,
    }

    r1 = AdmissionGuardrailAssessmentService.assess_admission(**kwargs)
    r2 = AdmissionGuardrailAssessmentService.assess_admission(**kwargs)

    assert r1["severity"] == r2["severity"]
    assert r1["flags"] == r2["flags"]
    assert r1["rn_explanation"] == r2["rn_explanation"]
    assert r1["guardrail_mode"] == r2["guardrail_mode"]