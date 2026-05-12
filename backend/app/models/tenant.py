from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import BaseModel


class Tenant(BaseModel):
    __tablename__ = "tenants"

    legal_name = Column(String, nullable=False)
    display_name = Column(String, nullable=False)
    status = Column(String, nullable=False, default="ACTIVE")