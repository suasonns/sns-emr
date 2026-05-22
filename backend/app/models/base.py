import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class TenantScoped:
    """
    Marker mixin for tenant-isolated models.

    Any model inheriting this will automatically
    receive tenant filtering via the global tenant guard.
    """
    tenant_id: UUID


class BaseModel(Base):
    __abstract__ = True

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )