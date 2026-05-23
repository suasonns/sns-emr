from sqlalchemy import Column, String, Boolean, DateTime, text
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class TenantRuleToggle(Base):
    __tablename__ = "tenant_rule_toggles"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))

    # MUST match DB column type (TEXT/VARCHAR)
    tenant_id = Column(String, nullable=False, index=True)

    workflow = Column(String(32), nullable=False, index=True)
    rule_id = Column(String(128), nullable=False, index=True)
    enabled = Column(Boolean, nullable=False, server_default=text("false"))

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))

    created_by = Column(UUID(as_uuid=True), nullable=True)