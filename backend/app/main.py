from fastapi import FastAPI, Depends

# ------------------------------------------------------
# CRITICAL: Load SQLAlchemy model registry FIRST
# This guarantees all FK targets exist in Base.metadata
# ------------------------------------------------------
import app.models  # noqa: F401

from app.core.audit_middleware import audit_middleware
from app.dependencies.tenant import inject_tenant

# ------------------------------------------------------
# API routers (import once)
# ------------------------------------------------------
from app.api import auth
from app.api import auth_whoami
from app.api import patients
from app.api import visits
from app.api import notes
from app.api import medications
from app.api import chha_pocs
from app.api import f2f
from app.api import certifications
from app.api import benefits
from app.api import compliance
from app.api import survey
from app.api import documents
from app.api import admin_reminders

# ------------------------------------------------------
# FastAPI app
# ------------------------------------------------------
app = FastAPI(
    title="SNS Hospice EMR",
    version="0.1.0",
)

# ------------------------------------------------------
# Global middleware
# ------------------------------------------------------
app.middleware("http")(audit_middleware)

# ------------------------------------------------------
# Router registration
#
# Rules:
# - Auth + system routes do NOT require tenant
# - All clinical/business routes REQUIRE tenant
# ------------------------------------------------------

# --- System / Auth (NO tenant injection) ---
app.include_router(auth.router)
app.include_router(auth_whoami.router)

# --- Tenant‑scoped business routers ---
tenant_dep = Depends(inject_tenant)

app.include_router(patients.router, dependencies=[tenant_dep])
app.include_router(visits.router, dependencies=[tenant_dep])
app.include_router(notes.router, dependencies=[tenant_dep])
app.include_router(medications.router, dependencies=[tenant_dep])
app.include_router(chha_pocs.router, dependencies=[tenant_dep])
app.include_router(f2f.router, dependencies=[tenant_dep])
app.include_router(certifications.router, dependencies=[tenant_dep])
app.include_router(benefits.router, dependencies=[tenant_dep])
app.include_router(compliance.router, dependencies=[tenant_dep])
app.include_router(survey.router, dependencies=[tenant_dep])
app.include_router(documents.router, dependencies=[tenant_dep])
app.include_router(admin_reminders.router, dependencies=[tenant_dep])

# ------------------------------------------------------
# System endpoints (NO tenant)
# ------------------------------------------------------
@app.get("/health", tags=["system"])
def health_check():
    return {"status": "ok"}

@app.get("/", tags=["system"])
def root():
    return {
        "status": "ok",
        "service": "SNS EMR Backend",
        "environment": "development",
    }