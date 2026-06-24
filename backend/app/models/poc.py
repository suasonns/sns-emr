"""
Enterprise-grade Plan of Care (POC) problem templates.

Design principles:
- Compliance-safe (CMS / ACHC / Joint Commission)
- Audit-ready (timestamps, lifecycle flags)
- Schema-aligned (matches Alembic)
- Indentation-safe (ASCII only)
"""

from sqlalchemy import Boolean, Column, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func, text

from app.db.base import Base


class POCProblemTemplate(Base):
    __tablename__ = "poc_problem_templates"

    # ------------------------------------------------------------------
    # Primary key
    # ------------------------------------------------------------------
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    # ------------------------------------------------------------------
    # Clinical classification
    # ------------------------------------------------------------------
    condition = Column(
        Text,
        nullable=False,
        doc="Primary condition this POC problem applies to (e.g., COPD, CHF, DEMENTIA)",
    )

    problem_label = Column(
        Text,
        nullable=False,
        doc="Human-readable Plan of Care problem statement",
    )

    # ------------------------------------------------------------------
    # Lifecycle / governance
    # ------------------------------------------------------------------
    is_active = Column(
        Boolean,
        nullable=False,
        server_default=text("true"),
        doc="Soft-disable flag; inactive templates are ignored but retained for audit",
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        doc="Creation timestamp (audit-safe)",
    )

    # ------------------------------------------------------------------
    # Enterprise safety helpers (NO DB side effects)
    # ------------------------------------------------------------------
    def as_dict(self) -> dict:
        """
        Safe serializer for API responses.
        Explicit fields only (prevents accidental PHI leaks).
        """
        return {
            "id": str(self.id),
            "condition": self.condition,
            "problem_label": self.problem_label,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }