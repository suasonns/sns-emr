from fastapi import FastAPI, Depends

from app.dependencies.tenant import inject_tenant

# ---------------------------------------------------------------------
# DOMAIN ROUTERS
# ---------------------------------------------------------------------
from app.api.eligibility.routes import router as eligibility_router
from app.api.rules.routes import router as rules_router
from app.api.regulatory.reports import router as regulatory_router

# ✅ ADD THIS
from app.api.dev_test import router as dev_test_router

# ---------------------------------------------------------------------
# EXISTING ROUTERS
# ---------------------------------------------------------------------
from app.api import (
    auth,
    auth_whoami,
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


def register_routers(app: FastAPI) -> None:
    """
    Central router registration.

    Guarantees:
    - Single routing surface
    - Tenant enforcement consistency
    - Strict tenant isolation
    """

    # -----------------------------------------------------------------
    # SYSTEM ROUTES (NO TENANT)
    # -----------------------------------------------------------------
    app.include_router(auth.router)
    app.include_router(auth_whoami.router)

    # -----------------------------------------------------------------
    # TENANT-SCOPED ROUTES
    # -----------------------------------------------------------------
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
        eligibility_router,
        rules_router,
        regulatory_router,
        dev_test_router,  # ✅ THIS FIX
    ]

    for route in tenant_routes:
        app.include_router(
            route,
            dependencies=[Depends(inject_tenant)],
        )