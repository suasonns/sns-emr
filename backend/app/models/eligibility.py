"""
Enterprise-grade hospice eligibility models.

Design principles:
- Compliance-first (CMS CoPs, ACHC, Joint Commission)
- Audit-safe (immutable assessment records)
- Schema-aligned (NO drift from Alembic)
- Forward-compatible (ADR, IDG, POC linkage)
- Indentation-safe (ASCII only)
"""

from sqlalchemy import Boolean, Column, DateTime, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func, text

from app.db.base import Base


# ---------------------------------------------------------------------
# Eligibility Ruleset (DEFINITION)
# ---------------------------------------------------------------------
class EligibilityRuleset(Base):
    __tablename__ = "eligibility_rulesets"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    ruleset_id = Column(Text, nullable=False)
    ruleset_version = Column(Text, nullable=False)
    condition = Column(Text, nullable=False)
    jurisdiction = Column(
        Text,
        nullable=False,
        server_default=text("'ANY'"),
    )

    ruleset_json = Column(JSONB, nullable=False)

    is_active = Column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    created_by = Column(Text, nullable=True)


# ---------------------------------------------------------------------
# Eligibility Assessment (AUDIT‑CRITICAL, WRITE‑ONCE)
# ---------------------------------------------------------------------
class EligibilityAssessment(Base):
    __tablename__ = "eligibility_assessments"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    patient_id = Column(
        UUID(as_uuid=True),
        nullable=False,
    )

    ruleset_id = Column(Text, nullable=False)
    ruleset_version = Column(Text, nullable=False)

    eligible = Column(Boolean, nullable=False)

    score = Column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )

    observations_snapshot = Column(
        JSONB,
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    created_by = Column(Text, nullable=True)
