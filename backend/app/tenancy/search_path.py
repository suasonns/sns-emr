import re
from sqlalchemy import text

# Allow only safe PostgreSQL identifiers
_SAFE_SCHEMA = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


def set_tenant_search_path(db, tenant_schema: str) -> None:
    """
    ✅ ENTERPRISE-GRADE TENANT SEARCH PATH SETTER

    Why this uses SET (not SET LOCAL):
    - SQLAlchemy ORM does not guarantee a transaction is started
    - SET LOCAL may be silently ignored
    - SET is deterministic for the connection

    Leak prevention is handled by explicitly resetting search_path
    when the session is closed.
    """

    if not tenant_schema or not _SAFE_SCHEMA.match(tenant_schema):
        raise ValueError(f"Unsafe tenant schema name: {tenant_schema!r}")

    # Deterministically route all unqualified table names
    db.execute(
        text(f'SET search_path TO "{tenant_schema}", public')
    )