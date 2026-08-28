# ---------------------------------------------------------------------
# ENVIRONMENT LOADING (MUST BE FIRST)
# ---------------------------------------------------------------------

from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).resolve().parents[1] / ".env.local"
# Real environment variables (shell / CI / cloud) always win over dotenv files.
load_dotenv(dotenv_path=env_path, override=False)


"""
SNS Hospice EMR – FastAPI application entrypoint.
Enterprise-grade initialization (stable + deterministic).
"""


# ---------------------------------------------------------------------
# ENVIRONMENT SAFETY GUARD (CRITICAL)
# ---------------------------------------------------------------------

import os


def validate_environment_safety() -> None:
    env = os.getenv("ENVIRONMENT", "").lower()
    bypass = os.getenv("ALLOW_DEV_DASHBOARD_BYPASS", "").lower()

    if env != "development" and bypass == "true":
        raise RuntimeError(
            "❌ CRITICAL SECURITY ERROR: DEV DASHBOARD BYPASS ENABLED OUTSIDE DEVELOPMENT"
        )


# ✅ RUN IMMEDIATELY AFTER ENV LOAD
validate_environment_safety()


# ---------------------------------------------------------------------
# CORE IMPORTS
# ---------------------------------------------------------------------

import asyncio
import hashlib
import json
import logging
import re
import subprocess
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Set

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.services.overdue_service import mark_overdue_poc_tasks
from app.core.tenant_routing_middleware import TenantRoutingMiddleware


# ---------------------------------------------------------------------
# LOGGING CONFIG
# ---------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger("sns_emr")


# ---------------------------------------------------------------------
# STARTUP STATUS
# ---------------------------------------------------------------------

STARTUP_STATUS: Dict[str, Any] = {
    "started_at_utc": None,
    "checks_passed": False,
    "alembic_current": None,
    "alembic_heads": None,
    "schema_hash_sha256": None,
    "db_probe_ok": False,
    "model_schema_ok": False,
    "scheduler_started": False,
    "error": None,
    "warnings": [],
}


# ---------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------

def _alembic_revision_ids(output: str) -> Set[str]:
    return set(re.findall(r"\b[0-9a-f]{7,40}\b", output.lower()))


def _backend_root_dir() -> Path:
    return Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------
# STARTUP MIGRATION (OPT-IN)
# ---------------------------------------------------------------------

def run_migrations_on_start() -> None:
    """
    Applies migrations before the startup checks when RUN_MIGRATIONS_ON_START
    is set, so a fresh environment can build its own schema without a separate
    pre-deploy step.
    """

    import os

    if os.getenv("RUN_MIGRATIONS_ON_START", "").lower() not in {"1", "true"}:
        return

    from alembic import command
    from alembic.config import Config as AlembicConfig

    backend_root = _backend_root_dir()
    ini_path = backend_root / "alembic.ini"

    if not ini_path.is_file():
        raise RuntimeError(f"❌ Alembic config not found: {ini_path}")

    alembic_cfg = AlembicConfig(str(ini_path))
    alembic_cfg.set_main_option("script_location", str(backend_root / "alembic"))

    logger.info("Running database migrations on startup")
    command.upgrade(alembic_cfg, "head")
    STARTUP_STATUS["migrations_applied_on_start"] = True


def bootstrap_development_logins_on_start() -> None:
    from app.core.database import SessionLocal
    from app.services.admin_bootstrap_service import provision_development_logins

    db = SessionLocal()
    try:
        if provision_development_logins(db):
            logger.info("Configured development login identities provisioned")
            STARTUP_STATUS["admin_bootstrapped_on_start"] = True
    finally:
        db.close()


# ---------------------------------------------------------------------
# ALEMBIC CHECK (HARD STOP)
# ---------------------------------------------------------------------

def assert_alembic_in_sync() -> None:
    """
    Ensures that the database schema is fully migrated to the latest revision.
    Hard fails if drift is detected.
    """

    import os

    from alembic.config import Config as AlembicConfig
    from alembic.runtime.migration import MigrationContext
    from alembic.script import ScriptDirectory

    # -----------------------------------------------------
    # OPTIONAL SKIP (ONLY FOR LOCAL / CI OVERRIDE)
    # -----------------------------------------------------
    if os.getenv("SKIP_ALEMBIC_CHECK", "").lower() in {"1", "true"}:
        return

    backend_root = _backend_root_dir()
    ini_path = backend_root / "alembic.ini"

    if not ini_path.is_file():
        raise RuntimeError(f"❌ Alembic config not found: {ini_path}")

    try:
        # -----------------------------------------------------
        # HEAD REVISIONS (FROM MIGRATION SCRIPTS)
        # -----------------------------------------------------
        alembic_cfg = AlembicConfig(str(ini_path))
        # script_location may be ini-relative; anchor it to the backend root
        alembic_cfg.set_main_option("script_location", str(backend_root / "alembic"))

        script = ScriptDirectory.from_config(alembic_cfg)
        head_set = set(script.get_heads())

        # -----------------------------------------------------
        # CURRENT REVISIONS (FROM alembic_version TABLE)
        # -----------------------------------------------------
        from app.core.database import engine

        with engine.connect() as connection:
            context = MigrationContext.configure(connection)
            current_set = set(context.get_current_heads())

        STARTUP_STATUS["alembic_current"] = sorted(current_set)
        STARTUP_STATUS["alembic_heads"] = sorted(head_set)

        # -----------------------------------------------------
        # VALIDATION
        # -----------------------------------------------------
        if not head_set:
            raise RuntimeError(
                f"❌ No Alembic head revisions detected in {backend_root / 'alembic'}"
            )

        if not current_set:
            raise RuntimeError(
                "❌ Database has no Alembic revision stamped "
                f"(expected_heads={sorted(head_set)}). Run `alembic upgrade head`."
            )

        if current_set != head_set:
            raise RuntimeError(
                f"❌ DATABASE SCHEMA DRIFT DETECTED — "
                f"current={sorted(current_set)} expected_heads={sorted(head_set)}"
            )

    except Exception as e:
        # -----------------------------------------------------
        # ENTERPRISE ERROR TRACEABILITY
        # -----------------------------------------------------
        error_msg = str(e)

        STARTUP_STATUS["warnings"].append(
            {"alembic_check_error": error_msg}
        )

        raise

# ---------------------------------------------------------------------
# DB PROBE
# ---------------------------------------------------------------------

def assert_db_probe() -> None:
    """
    Verifies database connectivity and basic query execution.
    Safe for production: no writes, no side effects, deterministic.
    """

    from app.db.session import SessionLocal
    from sqlalchemy import text

    db = SessionLocal()

    try:
        # -----------------------------------------------------
        # BASIC CONNECTIVITY TEST (READ-ONLY)
        # -----------------------------------------------------
        db.execute(text("SELECT 1"))

        # -----------------------------------------------------
        # SUCCESS FLAG
        # -----------------------------------------------------
        STARTUP_STATUS["db_probe_ok"] = True

    except Exception as e:
        # -----------------------------------------------------
        # STRUCTURED ERROR HANDLING (CRITICAL)
        # -----------------------------------------------------
        error_msg = f"db-probe-failed: {str(e)}"

        STARTUP_STATUS["db_probe_ok"] = False
        STARTUP_STATUS["warnings"].append(
            {"db_probe_error": error_msg}
        )

        raise RuntimeError(
            f"❌ DATABASE PROBE FAILED — {error_msg}"
        )

    finally:
        # -----------------------------------------------------
        # GUARANTEED CLEANUP
        # -----------------------------------------------------
        db.close()


# ---------------------------------------------------------------------
# MODEL DRIFT CHECK (WARNING ONLY)
# ---------------------------------------------------------------------

def check_model_schema_alignment() -> None:
    from app.db.session import SessionLocal
    from app.db.base import Base
    import app.models  # ensures models are registered

    db = SessionLocal()
    try:
        rows = db.execute(
            text(
                """
                SELECT
                    c.relname AS table_name,
                    a.attname AS column_name
                FROM pg_class c
                JOIN pg_namespace n
                    ON n.oid = c.relnamespace
                JOIN pg_attribute a
                    ON a.attrelid = c.oid
                WHERE
                    n.nspname = 'public'
                    AND c.relkind = 'r'
                    AND a.attnum > 0
                    AND NOT a.attisdropped
                """
            )
        ).fetchall()

        # -----------------------------------------------------
        # BUILD DB TABLE MAP
        # -----------------------------------------------------
        db_tables: Dict[str, Set[str]] = {}

        for table_name, column_name in rows:
            db_tables.setdefault(table_name, set()).add(column_name)

        missing_tables = []
        missing_columns = []

        # -----------------------------------------------------
        # COMPARE MODEL vs DB
        # -----------------------------------------------------
        for table in Base.metadata.tables.values():
            table_name = table.name

            if table_name not in db_tables:
                missing_tables.append(table_name)
                continue

            db_cols = db_tables[table_name]

            for col in table.columns:
                if col.name not in db_cols:
                    missing_columns.append(f"{table_name}.{col.name}")

        # -----------------------------------------------------
        # RESULT HANDLING
        # -----------------------------------------------------
        if missing_tables or missing_columns:
            warning = {
                "missing_tables": missing_tables,
                "missing_columns": missing_columns,
            }

            STARTUP_STATUS["warnings"].append(warning)

            logger.warning(
                "⚠️ MODEL ↔ DB drift detected (non-blocking): %s",
                warning,
            )
        else:
            STARTUP_STATUS["model_schema_ok"] = True

    except Exception as e:
        # -----------------------------------------------------
        # HARDENED ERROR HANDLING (ENTERPRISE REQUIRED)
        # -----------------------------------------------------
        error_msg = f"model-schema-check-failed: {str(e)}"

        STARTUP_STATUS["warnings"].append(
            {"model_schema_check_error": error_msg}
        )

        logger.exception("⚠️ Model-schema alignment check failed")

    finally:
        db.close()


# ---------------------------------------------------------------------
# SCHEMA HASH
# ---------------------------------------------------------------------

def log_schema_hash() -> None:
    """
    Computes a deterministic hash of the database schema.

    Enterprise-grade:
    - stable ordering
    - extended schema coverage
    - environment-consistent hashing
    - audit-safe logging
    """

    from app.db.session import SessionLocal
    from sqlalchemy import text
    import hashlib
    import json

    db = SessionLocal()

    try:
        # -----------------------------------------------------
        # FETCH SCHEMA (DETERMINISTIC ORDER)
        # -----------------------------------------------------
        rows = db.execute(
            text(
                """
                SELECT
                    table_name,
                    column_name,
                    data_type,
                    is_nullable,
                    column_default,
                    ordinal_position
                FROM information_schema.columns
                WHERE table_schema = 'public'
                ORDER BY table_name, ordinal_position
                """
            )
        ).fetchall()

        # -----------------------------------------------------
        # BUILD PAYLOAD
        # -----------------------------------------------------
        payload = [
            {
                "table": r[0],
                "column": r[1],
                "type": r[2],
                "nullable": r[3],
                "default": r[4],
                "position": r[5],
            }
            for r in rows
        ]

        # -----------------------------------------------------
        # STABLE HASH GENERATION
        # -----------------------------------------------------
        schema_hash = hashlib.sha256(
            json.dumps(payload, sort_keys=True).encode("utf-8")
        ).hexdigest()

        # -----------------------------------------------------
        # STORE + LOG
        # -----------------------------------------------------
        STARTUP_STATUS["schema_hash_sha256"] = schema_hash
        logger.info("✅ schema hash: %s", schema_hash)

    except Exception as e:
        # -----------------------------------------------------
        # ERROR TRACEABILITY (CRITICAL)
        # -----------------------------------------------------
        error_msg = f"schema-hash-failed: {str(e)}"

        STARTUP_STATUS["warnings"].append(
            {"schema_hash_error": error_msg}
        )

        logger.exception("⚠️ Schema hash computation failed")

    finally:
        db.close()


# ---------------------------------------------------------------------
# LIFESPAN
# ---------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    STARTUP_STATUS["started_at_utc"] = datetime.now(timezone.utc).isoformat()

    scheduler_task = None
    document_recovery_task = None

    try:
        # -------------------------------------------------------------
        # HARD STARTUP CHECKS
        # -------------------------------------------------------------
        run_migrations_on_start()
        bootstrap_development_logins_on_start()
        assert_alembic_in_sync()
        assert_db_probe()
        check_model_schema_alignment()
        log_schema_hash()

        STARTUP_STATUS["checks_passed"] = True
        logger.info("✅ SNS EMR started")

        # -------------------------------------------------------------
        # START OVERDUE SCHEDULER ONLY AFTER SUCCESSFUL INIT
        # -------------------------------------------------------------
        try:
            from app.services.task_scheduler import overdue_scheduler

            scheduler_task = asyncio.create_task(overdue_scheduler())
            STARTUP_STATUS["scheduler_started"] = True
            logger.info("✅ Overdue scheduler started")

        except Exception as scheduler_exc:
            STARTUP_STATUS["warnings"].append(
                {"scheduler_start_failed": str(scheduler_exc)}
            )
            logger.warning(
                "⚠️ Overdue scheduler failed to start (non-blocking): %s",
                scheduler_exc,
            )

        # -------------------------------------------------------------
        # PHASE A DURABILITY: recover any document stuck in
        # PENDING/PROCESSING/FAILED from before this restart, then start
        # the periodic sweep so structured-finding generation + RNICA
        # population always eventually complete, even after a crash or
        # a transient AI-service outage.
        # -------------------------------------------------------------
        try:
            from app.db.session import SessionLocal as _SessionLocal
            from app.services.evidence.recovery_service import recover_documents
            from app.services.document_recovery_scheduler import document_recovery_scheduler

            startup_recovery_db = _SessionLocal()
            try:
                startup_recovery_result = recover_documents(startup_recovery_db)
                if startup_recovery_result["examined"]:
                    logger.info(
                        "✅ Startup document recovery: examined=%s recovered=%s still_failed=%s",
                        startup_recovery_result["examined"],
                        len(startup_recovery_result["recovered"]),
                        len(startup_recovery_result["still_failed"]),
                    )
            finally:
                startup_recovery_db.close()

            document_recovery_task = asyncio.create_task(document_recovery_scheduler())
            STARTUP_STATUS["document_recovery_scheduler_started"] = True
            logger.info("✅ Document recovery scheduler started")

        except Exception as recovery_exc:
            document_recovery_task = None
            STARTUP_STATUS["warnings"].append(
                {"document_recovery_scheduler_start_failed": str(recovery_exc)}
            )
            logger.warning(
                "⚠️ Document recovery scheduler failed to start (non-blocking): %s",
                recovery_exc,
            )

        yield


    except Exception as e:
        # -------------------------------------------------------------
        # STRUCTURED STARTUP FAILURE RECORDING
        # -------------------------------------------------------------
        STARTUP_STATUS["error"] = str(e)
        logger.exception("🛑 Startup failed")
        raise

    finally:
        # -------------------------------------------------------------
        # CLEAN SHUTDOWN
        # -------------------------------------------------------------
        if scheduler_task is not None:
            scheduler_task.cancel()
            try:
                await scheduler_task
            except asyncio.CancelledError:
                logger.info("✅ Overdue scheduler stopped")
            except Exception as shutdown_exc:
                STARTUP_STATUS["warnings"].append(
                    {"scheduler_shutdown_failed": str(shutdown_exc)}
                )
                logger.warning(
                    "⚠️ Overdue scheduler shutdown issue: %s",
                    shutdown_exc,
                )

        if document_recovery_task is not None:
            document_recovery_task.cancel()
            try:
                await document_recovery_task
            except asyncio.CancelledError:
                logger.info("✅ Document recovery scheduler stopped")
            except Exception as shutdown_exc:
                STARTUP_STATUS["warnings"].append(
                    {"document_recovery_scheduler_shutdown_failed": str(shutdown_exc)}
                )
                logger.warning(
                    "⚠️ Document recovery scheduler shutdown issue: %s",
                    shutdown_exc,
                )


# ---------------------------------------------------------------------
# APP
# ---------------------------------------------------------------------

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

ENV = os.getenv("ENVIRONMENT", "development").lower()

fastapi_app = FastAPI(
    title="SNS Hospice EMR",
    version="1.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------
# MODELS (ENSURE REGISTRATION)
# ---------------------------------------------------------------------

import app.models  # noqa


# ---------------------------------------------------------------------
# MIDDLEWARE
# ---------------------------------------------------------------------

# ✅ SECURE CORS (ENV-BASED)
def _allowed_origins() -> list[str]:
    raw = (
        os.getenv("CORS_ALLOWED_ORIGINS")
        or os.getenv("ALLOWED_ORIGINS")
        or os.getenv("FRONTEND_URL")
        or os.getenv("APP_URL")
        or ""
    )

    origins = [item.strip() for item in raw.split(",") if item.strip()]
    if origins:
        return origins

    if ENV == "production":
        return [
            "http://localhost:5173",
            "http://localhost:4173",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:4173",
        ]

    return [
        "http://localhost:5173",
        "http://localhost:4173",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:4173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.core.middleware.clinical_access_guard import clinical_access_guard
from app.core.document_upload_limit import DocumentUploadLimitMiddleware
from app.core.recording_upload_limit import RecordingUploadLimitMiddleware

fastapi_app.middleware("http")(clinical_access_guard)
fastapi_app.add_middleware(DocumentUploadLimitMiddleware)
fastapi_app.add_middleware(RecordingUploadLimitMiddleware)


# ✅ TENANT ROUTING (ENABLE IF REQUIRED)
# from app.core.tenant_routing_middleware import TenantRoutingMiddleware
# fastapi_app.add_middleware(TenantRoutingMiddleware)


# ---------------------------------------------------------------------
# ROUTERS
# ---------------------------------------------------------------------

from app.api.registry import register_routers

register_routers(fastapi_app)

# Backward-compatible ASGI alias for tooling that expects `app.main:app`.
# Keep this after imports so the package name `app` is not clobbered by earlier
# `import app.*` statements.
app = fastapi_app


# ---------------------------------------------------------------------
# HEALTH ENDPOINTS
# ---------------------------------------------------------------------

@fastapi_app.get("/health")
def health():
    """
    Lightweight health check (load balancer safe).
    """
    return {
        "status": "ok",
        "environment": ENV,
    }


@fastapi_app.get("/system/startup-status")
def startup_status():
    """
    Full startup diagnostics (internal use).
    """
    return STARTUP_STATUS


@fastapi_app.get("/system/ready")
def readiness_check():
    """
    Production readiness probe:
    reflects real system state.
    """
    return {
        "ready": STARTUP_STATUS.get("checks_passed", False),
        "db": STARTUP_STATUS.get("db_probe_ok", False),
        "scheduler": STARTUP_STATUS.get("scheduler_started", False),
    }
