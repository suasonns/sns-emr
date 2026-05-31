import uuid
import pytest
from datetime import datetime, timezone

from sqlalchemy import text

from app.models.user import User


@pytest.fixture
def ensure_test_user(db_session):
    """
    Enterprise-safe fixture.

    Ensures at least one User exists for the active tenant so
    visits.provider_id (FK to users.id) can be satisfied.
    """
    tenant_id = db_session.info.get("tenant_id")
    assert tenant_id, "db_session.info['tenant_id'] must be set"

    # Try to find existing user
    user = (
        db_session.query(User)
        .filter(User.tenant_id == tenant_id)
        .first()
    )
    if user:
        return user

    # Create deterministic test user
    user = User(
        id=uuid.uuid5(uuid.NAMESPACE_DNS, f"test-user-{tenant_id}"),
        tenant_id=tenant_id,
        email=f"test-user-{tenant_id}@example.com",
        full_name="Test RN User",
        role="RN",
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(user)
    db_session.commit()
    return user
