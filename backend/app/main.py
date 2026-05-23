# ---------------------------------------------------------------------
# Environment loading (MUST be first)
# ---------------------------------------------------------------------
from dotenv import load_dotenv

load_dotenv(".env.local")
load_dotenv()

"""
SNS Hospice EMR – FastAPI application entrypoint.

Enterprise guarantees:
- SQLAlchemy model registry is loaded BEFORE app startup
- FK targets are resolved for Alembic + runtime
- Tenant isolation is enforced on all clinical/business routes
- Compliance-critical engines (Eligibility, IDG, POC) are explicit
"""

from fastapi import FastAPI, Depends

# ---------------------------------------------------------------------
# FastAPI application instance
# IMPORTANT: Do NOT name this `app` (conflicts with Python package)
# ---------------------------------------------------------------------
api = FastAPI(
    title="SNS Hospice EMR",
    version="0.1.0",
)

# ---------------------------------------------------------------------
# LCD configuration loader (COMPLIANCE-CRITICAL)
# ---------------------------------------------------------------------
from app.config.lcd.loader import load_lcd_configs, LCDConfigError


@api.on_event("startup")
def load_lcd_configuration() -> None:
    try:
        api.state.lcd_configs = load_lcd_configs()
    except LCDConfigError as e:
        # HARD STOP — system must not run without LCD logic
        raise RuntimeError(f"LCD CONFIGURATION ERROR: {e}") from e


# ---------------------------------------------------------------------
# CRITICAL: Load SQLAlchemy model registry FIRST
# This guarantees all FK targets exist in Base.metadata
# DO NOT MOVE THIS IMPORT
# ---------------------------------------------------------------------
import app.models  # noqa: F401


# ---------------------------------------------------------------------
# Middleware & dependencies
# ---------------------------------------------------------------------
from app.core.audit_middleware import audit_middleware
from app.dependencies.tenant import inject_tenant


# ---------------------------------------------------------------------
# API routers
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

from app.routers.eligibility import router as eligibility_router
from app.routers import rules as rules_router


# ---------------------------------------------------------------------
# Global middleware
# ---------------------------------------------------------------------
api.middleware("http")(audit_middleware)


# ---------------------------------------------------------------------
# Router registration
# ---------------------------------------------------------------------

# --- System / Auth (NO tenant) ---
api.include_router(auth.router)
api.include_router(auth_whoami.router)

# --- Tenant-scoped routes ---
tenant_dep = Depends(inject_tenant)

api.include_router(patients.router, dependencies=[tenant_dep])
api.include_router(visits.router, dependencies=[tenant_dep])
api.include_router(notes.router, dependencies=[tenant_dep])
api.include_router(medications.router, dependencies=[tenant_dep])

api.include_router(chha_pocs.router, dependencies=[tenant_dep])
api.include_router(f2f.router, dependencies=[tenant_dep])
api.include_router(certifications.router, dependencies=[tenant_dep])
api.include_router(benefits.router, dependencies=[tenant_dep])

api.include_router(compliance.router, dependencies=[tenant_dep])
api.include_router(survey.router, dependencies=[tenant_dep])
api.include_router(documents.router, dependencies=[tenant_dep])
api.include_router(admin_reminders.router, dependencies=[tenant_dep])

# --- Eligibility / LCD engine (COMPLIANCE-CRITICAL) ---
api.include_router(eligibility_router, dependencies=[tenant_dep])

# --- Rules dry-run (NO enforcement) ---
api.include_router(rules_router.router, dependencies=[tenant_dep])


# ---------------------------------------------------------------------
# System endpoints (NO tenant)
# ---------------------------------------------------------------------
@api.get("/health", tags=["system"])
def health_check():
    return {"status": "ok"}


@api.get("/", tags=["system"])
def root():
    return {
        "status": "ok",
        "service": "SNS EMR Backend",
        "environment": "development",
    }