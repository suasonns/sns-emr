from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import BaseModel


class Tenant(BaseModel):
    __tablename__ = "tenants"

    legal_name = Column(String, nullable=False)
    display_name = Column(String, nullable=False)

    # Compliance-safe audit attribution
    # IMPORTANT:
    # - Nullable to allow tenant bootstrap
    # - NO ForeignKey to users.id (prevents FK cycle)
    created_by = Column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    status = Column(
        String,
        nullable=False,
        default="ACTIVE",
    )
