from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import BaseModel
from app.models.tenant import Tenant  # ensures table registration


class User(BaseModel):
    __tablename__ = "users"

    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    email = Column(String, nullable=False, unique=True)
    full_name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    license_number = Column(String, nullable=True)

    active = Column(
        Boolean,
        nullable=False,
        default=True,
    )
