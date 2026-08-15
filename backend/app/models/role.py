# models/role.py

import uuid
from sqlalchemy import Column, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base


class Role(Base):
    __tablename__ = "roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interface_id = Column(UUID(as_uuid=True), ForeignKey("interfaces.id"), nullable=False)
    name = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
