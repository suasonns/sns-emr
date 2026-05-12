from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import BaseModel
from app.models.tenant import Tenant  # noqa: F401 (ensures tenants table is registered)


class User(BaseModel):
    __tablename__ = "users"

    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )

    email = Column(String, unique=True, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    license_number = Column(String, nullable=True)
    active = Column(Boolean, default=True, nullable=False)