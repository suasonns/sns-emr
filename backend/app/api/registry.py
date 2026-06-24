from fastapi import FastAPI

# SYSTEM / AUTH ROUTES
from app.api import auth, auth_whoami

# OWNER / SUPPORT
from app.api.support_reference import router as support_reference_router

# ADMIN
from app.api.admin.chart_export import router as admin_chart_export_router
from app.api.routes import forms

# COMMUNICATIONS LOG
from app.api.communications_log.router import router as communications_log_router

# CORE TENANT ROUTES
from app.api import (
    patients,
    visits,
    notes,
    medications,
    chha_pocs,
    f2f,
    certifications,
    benefits,
    compliance,
    survey,
    documents,
    admin_reminders,
    admission_authorization,
    med_reconciliation,
)

# DOMAIN / WORKFLOW
from app.api.eligibility.routes import router as eligibility_router
from app.api.rules.routes import router as rules_router
from app.api.regulatory.reports import router as regulatory_router
from app.api.safety_assessments import router as safety_assessments_router

# ENGINE LAYER
from app.api.clinical_notes.router import router as clinical_notes_router
from app.api.idg.router import router as idg_router
from app.api.dashboard.router import router as dashboard_router
from app.api.audit_dashboard import router as audit_dashboard_router
from app.api.clinical_translation import router as clinical_translation_router  # ✅ ADD THIS

# ✅ NEW TASK ROUTER (THIS IS THE FIX)
from app.api.tasks import router as tasks_router

# TASK ENGINE (existing)
from app.api.task_completion import router as task_completion_router
from app.api.task_scheduling import router as task_scheduling_router

# WORKFLOW
from app.api.patient_assignments import router as patient_assignments_router
from app.api.soc_orders import router as soc_orders_router

# EXTERNAL
from app.api.coverage import router as coverage_router
from app.api.external_substances import router as external_substances_router

# BILLING
from app.billing.api.billing_queue_router import router as billing_queue_router
from app.billing.api.tenant_router import router as tenant_router
from app.billing.api.export_router import router as export_router
from app.billing.api.claim_status_router import router as claim_status_router
from app.billing.api.audit_router import router as audit_router
from app.billing.api.billing_router import router as billing_router  # legacy last

# DEV / TEST
from app.api.dev_test import router as dev_test_router

# ADR / TPE (OPTIONAL)
try:
    from app.api.adr_exports import router as adr_exports_router
    from app.api.adr_readiness import router as adr_readiness_router
except Exception:  # pragma: no cover
    adr_exports_router = None
    adr_readiness_router = None


def register_routers(app: FastAPI) -> None:
    """
    Canonical router registry.
    """

    # =====================================================
    # Auth / system
    # =====================================================
    app.include_router(auth.router)
    app.include_router(auth_whoami.router)

    # =====================================================
    # Owner / support
    # =====================================================
    app.include_router(support_reference_router)

    # =====================================================
    # Admin
    # =====================================================
    app.include_router(admin_chart_export_router)

    # =====================================================
    # Optional ADR/TPE
    # =====================================================
    if adr_exports_router is not None:
        app.include_router(adr_exports_router)

    if adr_readiness_router is not None:
        app.include_router(adr_readiness_router)

    # =====================================================
    # Tenant + application routes
    # =====================================================
    tenant_routes = [
        patients.router,
        visits.router,
        forms.router,
        notes.router,
        communications_log_router,
        clinical_notes_router,
        idg_router,
        dashboard_router,
        clinical_translation_router,  # ✅ ADD THIS

        # ✅ ADD YOUR TASKS ROUTER HERE (CRITICAL)
        tasks_router,

        audit_dashboard_router,
        medications.router,
        chha_pocs.router,
        f2f.router,
        certifications.router,
        benefits.router,
        compliance.router,
        survey.router,
        documents.router,
        admin_reminders.router,
        admission_authorization.router,
        med_reconciliation.router,
        soc_orders_router,

        # Existing task system
        task_completion_router,
        task_scheduling_router,

        patient_assignments_router,
        eligibility_router,
        rules_router,
        regulatory_router,
        safety_assessments_router,
        coverage_router,
        external_substances_router,
        billing_queue_router,
        tenant_router,
        export_router,
        claim_status_router,
        audit_router,
        billing_router,
        dev_test_router,
    ]

    for router in tenant_routes:
        app.include_router(router)