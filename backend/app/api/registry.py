from fastapi import FastAPI

# -------------------------------------------------------------
# SYSTEM / AUTH ROUTES
# -------------------------------------------------------------
from app.api import auth, auth_whoami

# -------------------------------------------------------------
# CORE TENANT ROUTES
# -------------------------------------------------------------
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
)

# -------------------------------------------------------------
# DOMAIN / WORKFLOW ROUTES
# -------------------------------------------------------------
from app.api.eligibility.routes import router as eligibility_router
from app.api.rules.routes import router as rules_router
from app.api.regulatory.reports import router as regulatory_router
from app.api.safety_assessments import router as safety_assessments_router
from app.api.task_completion import router as task_completion_router

# -------------------------------------------------------------
# ASSIGNMENT + SOC + SCHEDULING
# -------------------------------------------------------------
from app.api.patient_assignments import router as patient_assignments_router
from app.api.soc_orders import router as soc_orders_router
from app.api.task_scheduling import router as task_scheduling_router

# -------------------------------------------------------------
# DEV / TEST
# -------------------------------------------------------------
from app.api.dev_test import router as dev_test_router

# -------------------------------------------------------------
# ✅ BILLING (STEP 4 ENGINE)
# -------------------------------------------------------------
from app.billing.api.billing_router import router as billing_router


def register_routers(app: FastAPI) -> None:
    """
    Central router registration.

    ENTERPRISE RULES:
    - No header-based tenant enforcement here
    - Tenant derived ONLY from authenticated identity
    - DB scoping handled by get_db_tenant
    """

    # -----------------------------
    # AUTH / SYSTEM
    # -----------------------------
    app.include_router(auth.router)
    app.include_router(auth_whoami.router)

    # -----------------------------
    # TENANT-SCOPED ROUTES
    # -----------------------------
    tenant_routes = [
        # Core clinical
        patients.router,
        visits.router,
        notes.router,
        medications.router,
        chha_pocs.router,
        f2f.router,
        certifications.router,
        benefits.router,
        compliance.router,
        survey.router,
        documents.router,
        admin_reminders.router,

        # Admission / SOC
        admission_authorization.router,

        # Task lifecycle
        task_completion_router,

        # Domain logic
        eligibility_router,
        rules_router,
        regulatory_router,

        # Workflow
        safety_assessments_router,
        patient_assignments_router,
        soc_orders_router,
        task_scheduling_router,

        # Dev
        dev_test_router,

        # ✅ ADD BILLING HERE
        billing_router,
    ]

    for route in tenant_routes:
        app.include_router(route)