# ---------------------------------------------------------------------
# ENVIRONMENT LOADING (MUST BE FIRST)
# ---------------------------------------------------------------------

from dotenv import load_dotenv

load_dotenv(".env.local")
load_dotenv()

"""
SNS Hospice EMR – FastAPI application entrypoint.
Enterprise-grade initialization (stable + deterministic).
"""

# ---------------------------------------------------------------------
# CORE IMPORTS
# ---------------------------------------------------------------------

import hashlib
import json
import logging
import os
import re
import subprocess
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Set

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

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
# ALEMBIC CHECK (HARD STOP)
# ---------------------------------------------------------------------

def assert_alembic_in_sync() -> None:
    if os.getenv("SKIP_ALEMBIC_CHECK", "").lower() in {"1", "true"}:
        return

    backend_root = _backend_root_dir()

    current = subprocess.run(
        ["alembic", "current"], capture_output=True, text=True, cwd=str(backend_root)
    )
    heads = subprocess.run(
        ["alembic", "heads"], capture_output=True, text=True, cwd=str(backend_root)
    )

    current_ids = _alembic_revision_ids(current.stdout)
    head_ids = _alembic_revision_ids(heads.stdout)

    STARTUP_STATUS["alembic_current"] = sorted(current_ids)
    STARTUP_STATUS["alembic_heads"] = sorted(head_ids)

    if current_ids != head_ids:
        raise RuntimeError("DATABASE SCHEMA DRIFT DETECTED — Alembic mismatch")

# ---------------------------------------------------------------------
# DB PROBE
# ---------------------------------------------------------------------

def assert_db_probe() -> None:
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        db.execute(text("CREATE TEMP TABLE IF NOT EXISTS sns_probe(x int)"))
        db.execute(text("INSERT INTO sns_probe(x) VALUES (1)"))
        db.rollback()
        STARTUP_STATUS["db_probe_ok"] = True
    finally:
        db.close()

# ---------------------------------------------------------------------
# ⚠️ MODEL DRIFT CHECK (WARNING ONLY)
# ---------------------------------------------------------------------

def check_model_schema_alignment() -> None:
    from app.db.session import SessionLocal
    from app.db.base import Base

    db = SessionLocal()
    try:
        rows = db.execute(
            text("""
                SELECT table_name, column_name
                FROM information_schema.columns
                WHERE table_schema='public'
            """)
        ).fetchall()

        db_tables: Dict[str, Set[str]] = {}
        for table_name, column_name in rows:
            db_tables.setdefault(table_name, set()).add(column_name)

        missing_tables = []
        missing_columns = []

        for table_name, table in Base.metadata.tables.items():
            if table_name not in db_tables:
                missing_tables.append(table_name)
                continue

            db_cols = db_tables[table_name]
            for col in table.columns:
                if col.name not in db_cols:
                    missing_columns.append(f"{table_name}.{col.name}")

        if missing_tables or missing_columns:
            warning = {
                "missing_tables": missing_tables,
                "missing_columns": missing_columns,
            }
            STARTUP_STATUS["warnings"].append(warning)
            logger.warning("⚠️ MODEL ↔ DB drift detected (non-blocking): %s", warning)
        else:
            STARTUP_STATUS["model_schema_ok"] = True
    finally:
        db.close()

# ---------------------------------------------------------------------
# SCHEMA HASH
# ---------------------------------------------------------------------

def log_schema_hash() -> None:
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        rows = db.execute(
            text("""
                SELECT table_name, column_name, data_type
                FROM information_schema.columns
                WHERE table_schema='public'
                ORDER BY table_name
            """)
        ).fetchall()

        payload = [{"t": r[0], "c": r[1], "d": r[2]} for r in rows]
        schema_hash = hashlib.sha256(json.dumps(payload).encode()).hexdigest()

        STARTUP_STATUS["schema_hash_sha256"] = schema_hash
        logger.info("✅ schema hash: %s", schema_hash)
    finally:
        db.close()

# ---------------------------------------------------------------------
# LIFESPAN
# ---------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    STARTUP_STATUS["started_at_utc"] = datetime.utcnow().isoformat()
    try:
        assert_alembic_in_sync()
        assert_db_probe()
        check_model_schema_alignment()
        log_schema_hash()

        STARTUP_STATUS["checks_passed"] = True
        logger.info("✅ SNS EMR started")
        yield
    except Exception as e:
        STARTUP_STATUS["error"] = str(e)
        logger.exception("🛑 Startup failed")
        raise

# ---------------------------------------------------------------------
# APP
# ---------------------------------------------------------------------

fastapi_app = FastAPI(
    title="SNS Hospice EMR",
    version="1.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------
# MODELS (REGISTER METADATA)
# ---------------------------------------------------------------------

import app.models  # noqa

# ---------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------
# ROUTERS
# ---------------------------------------------------------------------

from app.api.registry import register_routers

register_routers(fastapi_app)

# ---------------------------------------------------------------------
# HEALTH
# ---------------------------------------------------------------------

@fastapi_app.get("/health")
def health():
    return {"status": "ok"}

@fastapi_app.get("/system/startup-status")
def startup_status():
    return STARTUP_STATUS