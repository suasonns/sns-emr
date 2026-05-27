from fastapi import FastAPI

# -------------------------------------------------------------
# SYSTEM / AUTH ROUTES
# -------------------------------------------------------------
from app.api import auth, auth_whoami

# -------------------------------------------------------------
# CORE TENANT ROUTES (modules under app/api/*.py)
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
)

# -------------------------------------------------------------
# DOMAIN / WORKFLOW ROUTES (routers defined in their own modules)
# -------------------------------------------------------------
from app.api.eligibility.routes import router as eligibility_router
from app.api.rules.routes import router as rules_router
from app.api.regulatory.reports import router as regulatory_router
from app.api.safety_assessments import router as safety_assessments_router

# -------------------------------------------------------------
# ASSIGNMENT + SOC + SCHEDULING (NEW)
# -------------------------------------------------------------
from app.api.patient_assignments import router as patient_assignments_router
from app.api.soc_orders import router as soc_orders_router
from app.api.task_scheduling import router as task_scheduling_router

# -------------------------------------------------------------
# DEV / TEST
# -------------------------------------------------------------
from app.api.dev_test import router as dev_test_router


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

        # Domain routes
        eligibility_router,
        rules_router,
        regulatory_router,

        # Safety + SOC workflow
        safety_assessments_router,
        patient_assignments_router,
        soc_orders_router,
        task_scheduling_router,

        # Dev/Test (remove in prod if desired)
        dev_test_router,
    ]

    for route in tenant_routes:
        app.include_router(route)