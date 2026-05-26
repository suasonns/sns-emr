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

# ---------------------------------------------------------------------
# FastAPI instance (NO NAME COLLISION)
# ---------------------------------------------------------------------
fastapi_app = FastAPI(
    title="SNS Hospice EMR",
    version="0.1.0",
)

# ---------------------------------------------------------------------
# LCD configuration loader
# ---------------------------------------------------------------------
from app.config.lcd.loader import load_lcd_configs, LCDConfigError


@fastapi_app.on_event("startup")
def load_lcd_configuration() -> None:
    try:
        fastapi_app.state.lcd_configs = load_lcd_configs()
    except LCDConfigError as e:
        raise RuntimeError(f"LCD CONFIGURATION ERROR: {e}") from e


# ---------------------------------------------------------------------
# Load SQLAlchemy models FIRST
# ---------------------------------------------------------------------
import app.models  # noqa: F401

# ---------------------------------------------------------------------
# Load ORM tenant filters (CRITICAL)
# ---------------------------------------------------------------------
import app.core.tenant_orm_filters  # noqa: F401

# ---------------------------------------------------------------------
# Middleware
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


@fastapi_app.get("/", tags=["system"])
def root():
    return {
        "status": "ok",
        "service": "SNS EMR Backend",
        "environment": "development",
    }
