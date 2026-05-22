# app/core/database.py

from __future__ import annotations

import os
from typing import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker, with_loader_criteria

from app.core.tenant_context import get_current_tenant
from app.db.base import Base
from app.models.base import TenantScoped

# ---------------------------------------------------------------------
# Database URL (enterprise-grade: env first)
# ---------------------------------------------------------------------
# NOTE:
# - Set DATABASE_URL in the environment for real deployments.
# - Fallback is for local DEV only.
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://sns_user:sns_password@127.0.0.1:5433/sns_emr",
)

# ---------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------
engine = create_engine(
    DATABASE_URL,
    future=True,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    # Ensures schema-less model + FK strings resolve to public.*
    connect_args={"options": "-csearch_path=public"},
)

# ---------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)

# ---------------------------------------------------------------------
# Global Tenant Guard (ORM-level defense-in-depth)
#
# Enforces tenant isolation automatically for all models inheriting TenantScoped.
# Works with joins/aliases/eager loads via with_loader_criteria.
#
# Opt-out ONLY for trusted internal jobs:
#   stmt = stmt.execution_options(include_all_tenants=True)
# ---------------------------------------------------------------------
@event.listens_for(Session, "do_orm_execute")
def _tenant_guard(execute_state) -> None:
    if not execute_state.is_select:
        return

    if execute_state.execution_options.get("include_all_tenants", False):
        return

    tenant_id = get_current_tenant()
    if tenant_id is None:
        return

    stmt = execute_state.statement

    for mapper in Base.registry.mappers:
        cls = mapper.class_
        try:
            if issubclass(cls, TenantScoped):
                stmt = stmt.options(
                    with_loader_criteria(
                        cls,
                        lambda c: c.tenant_id == tenant_id,  # noqa: E731
                        include_aliases=True,
                    )
                )
        except TypeError:
            continue

    execute_state.statement = stmt

# ---------------------------------------------------------------------
# RLS Tenant Propagation (DB-level enforcement)
#
# Sets Postgres session variable used by RLS policies:
#   app.current_tenant = <tenant UUID>
#
# Uses SET LOCAL so the setting is scoped to the current transaction and
# is automatically cleared on commit/rollback (safe with pooled connections).
# ---------------------------------------------------------------------
@event.listens_for(Session, "after_begin")
def _set_rls_tenant(session: Session, transaction, connection) -> None:
    tenant_id = get_current_tenant()

    if tenant_id is None:
        connection.execute(text("RESET app.current_tenant"))
        return

    connection.execute(
        text("SET LOCAL app.current_tenant = :tenant_id"),
        {"tenant_id": str(tenant_id)},
    )

# ---------------------------------------------------------------------
# Dependency (FastAPI)
# ---------------------------------------------------------------------
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()