# ---------------------------------------------------------------------
# Environment loading (MUST be first)
# ---------------------------------------------------------------------
from dotenv import load_dotenv
load_dotenv(".env.local")
load_dotenv()

"""
SNS Hospice EMR – FastAPI application entrypoint.
"""

from fastapi import FastAPI

fastapi_app = FastAPI(
    title="SNS Hospice EMR",
    version="0.1.0",
)

# ---------------------------------------------------------------------
# Load SQLAlchemy models FIRST
# ---------------------------------------------------------------------
import app.models  # noqa: F401

# ---------------------------------------------------------------------
# Load ORM tenant filters (CRITICAL)
# ---------------------------------------------------------------------
import app.core.tenant_orm_filters  # noqa: F401

# ---------------------------------------------------------------------
# Audit middleware (OBSERVATION ONLY)
# ---------------------------------------------------------------------
from app.core.audit_middleware import audit_middleware
fastapi_app.middleware("http")(audit_middleware)

# ---------------------------------------------------------------------
# Router registration
# ---------------------------------------------------------------------
from app.api.registry import register_routers
register_routers(fastapi_app)

# ---------------------------------------------------------------------
# System endpoints
# ---------------------------------------------------------------------
@fastapi_app.get("/health", tags=["system"])
def health_check():
    return {"status": "ok"}