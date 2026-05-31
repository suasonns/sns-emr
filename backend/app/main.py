# ---------------------------------------------------------------------
# ENVIRONMENT LOADING (MUST BE FIRST)
# ---------------------------------------------------------------------
from dotenv import load_dotenv

load_dotenv(".env.local")
load_dotenv()

"""
SNS Hospice EMR – FastAPI application entrypoint.
"""

# ---------------------------------------------------------------------
# CORE IMPORTS
# ---------------------------------------------------------------------
import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager

logger = logging.getLogger("app")

# ---------------------------------------------------------------------
# LIFESPAN (ENTERPRISE STANDARD)
# ---------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("✅ SNS Hospice EMR started")
    yield
    logger.info("🛑 SNS Hospice EMR shutting down")

# ---------------------------------------------------------------------
# APP INIT (KEEP NAME STABLE)
# ---------------------------------------------------------------------
fastapi_app = FastAPI(
    title="SNS Hospice EMR",
    version="0.1.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------
# LOAD SQLALCHEMY MODELS FIRST
# ---------------------------------------------------------------------
try:
    import app.models  # noqa: F401
except Exception as e:
    raise RuntimeError(f"Failed to load models: {e}")

# ---------------------------------------------------------------------
# LOAD ORM TENANT FILTERS (CRITICAL)
# ---------------------------------------------------------------------
try:
    import app.core.tenant_orm_filters  # noqa: F401
except Exception as e:
    raise RuntimeError(f"Failed to load tenant ORM filters: {e}")

# ---------------------------------------------------------------------
# AUDIT MIDDLEWARE (OBSERVATION ONLY)
# ---------------------------------------------------------------------
from app.core.audit_middleware import audit_middleware

fastapi_app.middleware("http")(audit_middleware)

# ---------------------------------------------------------------------
# ROUTER REGISTRATION
# ---------------------------------------------------------------------
from app.api.registry import register_routers

register_routers(fastapi_app)

# ---------------------------------------------------------------------
# SYSTEM ENDPOINTS
# ---------------------------------------------------------------------
@fastapi_app.get("/health", tags=["system"])
def health_check():
    return {"status": "ok"}