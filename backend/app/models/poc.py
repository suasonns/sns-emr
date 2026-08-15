# =========================================================
# FILE: app/models/poc.py
# PURPOSE: Materialized Plan of Care projection tables
# STATUS: HARDENED / FK SAFE
# NOTE:
# - These are derived projection tables from plan_of_care_versions.snapshot_json
# - Problem -> Goal -> Intervention remains the normalized query/report layer
# =========================================================

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


def _utcnow():
    return datetime.now(timezone.utc)


class POCProblem(Base):
    """
    Materialized Plan of Care Problem.

    Purpose:
    - Stores a single problem generated from the diagnosis rules engine
      or added manually through RN / IDG updates
    - Anchors goals and interventions under a specific POC version

    Notes:
    - Python attribute names remain stable for application code.
    - DB column names are aligned to the current live database.
    """

    __tablename__ = "poc_problems"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "poc_version_id",
            "problem_code",
            "source_diagnosis_code",
            name="uq_poc_problems_version_code_dx",
        ),
        CheckConstraint(
            "diagnosis_context IN ('PRIMARY', 'SECONDARY', 'COMORBIDITY', 'CONTRIBUTING_CONDITION', 'MANUAL')",
            name="ck_poc_problems_diagnosis_context",
        ),
        CheckConstraint(
            "severity IN ('LOW', 'MODERATE', 'HIGH', 'CRITICAL', 'UNKNOWN')",
            name="ck_poc_problems_severity",
        ),
        CheckConstraint(
            "status IN ('ACTIVE', 'IMPROVING', 'RESOLVED', 'HISTORICAL', 'SUPERSEDED')",
            name="ck_poc_problems_status",
        ),
        CheckConstraint(
            "source_kind IN ('RULE_GENERATED', 'MANUAL', 'RN_UPDATE', 'IDG_UPDATE', 'SYSTEM')",
            name="ck_poc_problems_source_kind",
        ),
        Index("ix_poc_problems_tenant_id", "tenant_id"),
        Index("ix_poc_problems_version_id", "poc_version_id"),
        Index("ix_poc_problems_problem_code", "problem_code"),
        Index("ix_poc_problems_source_diagnosis_code", "source_diagnosis_code"),
        Index("ix_poc_problems_status", "status"),
        Index("ix_poc_problems_sort_order", "sort_order"),
    )

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )

    poc_version_id = Column(
        UUID(as_uuid=True),
        ForeignKey("plan_of_care_versions.id", ondelete="CASCADE"),
        nullable=False,
    )

    source_diagnosis_code = Column(
        String(20),
        nullable=True,
    )

    source_condition = Column(
        String(120),
        nullable=True,
    )

    diagnosis_context = Column(
        String(40),
        nullable=False,
        default="MANUAL",
    )

    rule_key = Column(
        String(50),
        nullable=True,
    )

    problem_code = Column(
        String(100),
        nullable=False,
    )

    label = Column(
        Text,
        nullable=False,
    )

    description = Column(
        Text,
        nullable=True,
    )

    severity = Column(
        String(20),
        nullable=False,
        default="UNKNOWN",
    )

    source_kind = Column(
        String(30),
        nullable=False,
        default="RULE_GENERATED",
    )

    is_rule_generated = Column(
        Boolean,
        nullable=False,
        default=True,
    )

    status = Column(
        String(20),
        nullable=False,
        default="ACTIVE",
    )

    sort_order = Column(
        Integer,
        nullable=False,
        default=100,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
    )

    created_by_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        onupdate=_utcnow,
    )

    updated_by_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    poc_version = relationship(
        "PlanOfCareVersion",
        back_populates="problems",
        foreign_keys=[poc_version_id],
    )

    goals = relationship(
        "POCGoal",
        back_populates="problem",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="POCGoal.sort_order",
    )


class POCGoal(Base):
    """
    Materialized Plan of Care Goal.

    Purpose:
    - Stores a goal under a single POC problem
    - Maps directly from rules engine goals[] or RN / IDG additions

    Notes:
    - Python attribute name stays `problem_id` for service compatibility
    - Physical DB column name is `poc_problem_id` to match current live DB
    """

    __tablename__ = "poc_goals"

    __table_args__ = (
        CheckConstraint(
            "status IN ('ACTIVE', 'MET', 'NOT_MET', 'HISTORICAL', 'SUPERSEDED')",
            name="ck_poc_goals_status",
        ),
        CheckConstraint(
            "source_kind IN ('RULE_GENERATED', 'MANUAL', 'RN_UPDATE', 'IDG_UPDATE', 'SYSTEM')",
            name="ck_poc_goals_source_kind",
        ),
        Index("ix_poc_goals_tenant_id", "tenant_id"),
        Index("ix_poc_goals_poc_problem_id", "poc_problem_id"),
        Index("ix_poc_goals_status", "status"),
        Index("ix_poc_goals_sort_order", "sort_order"),
    )

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Python attribute remains problem_id
    # Physical DB column is poc_problem_id
    problem_id = Column(
        "poc_problem_id",
        UUID(as_uuid=True),
        ForeignKey("poc_problems.id", ondelete="CASCADE"),
        nullable=False,
    )

    goal_text = Column(
        Text,
        nullable=False,
    )

    measurable_outcome = Column(
        Text,
        nullable=True,
    )

    target_timeframe = Column(
        String(100),
        nullable=True,
    )

    source_kind = Column(
        String(30),
        nullable=False,
        default="RULE_GENERATED",
    )

    is_rule_generated = Column(
        Boolean,
        nullable=False,
        default=True,
    )

    status = Column(
        String(20),
        nullable=False,
        default="ACTIVE",
    )

    sort_order = Column(
        Integer,
        nullable=False,
        default=100,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
    )

    created_by_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        onupdate=_utcnow,
    )

    updated_by_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    problem = relationship(
        "POCProblem",
        back_populates="goals",
        foreign_keys=[problem_id],
    )

    interventions = relationship(
        "POCIntervention",
        back_populates="goal",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="POCIntervention.sort_order",
    )


class POCIntervention(Base):
    """
    Materialized Plan of Care Intervention.

    Purpose:
    - Stores interventions under a goal
    - Maps directly from rules engine interventions[]
    - Preserves responsible discipline and optional frequency/instructions

    Notes:
    - Python attribute name stays `goal_id` for service compatibility
    - Physical DB column name is `poc_goal_id` to match current live DB
    """

    __tablename__ = "poc_interventions"

    __table_args__ = (
        CheckConstraint(
            "discipline IN ('RN', 'MSW', 'SC', 'LVN', 'HHA', 'MD', 'IDG', 'OTHER')",
            name="ck_poc_interventions_discipline",
        ),
        CheckConstraint(
            "status IN ('ACTIVE', 'COMPLETED', 'CANCELED', 'HISTORICAL', 'SUPERSEDED')",
            name="ck_poc_interventions_status",
        ),
        CheckConstraint(
            "source_kind IN ('RULE_GENERATED', 'MANUAL', 'RN_UPDATE', 'IDG_UPDATE', 'SYSTEM')",
            name="ck_poc_interventions_source_kind",
        ),
        Index("ix_poc_interventions_tenant_id", "tenant_id"),
        Index("ix_poc_interventions_poc_goal_id", "poc_goal_id"),
        Index("ix_poc_interventions_discipline", "discipline"),
        Index("ix_poc_interventions_status", "status"),
        Index("ix_poc_interventions_sort_order", "sort_order"),
    )

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Python attribute remains goal_id
    # Physical DB column is poc_goal_id
    goal_id = Column(
        "poc_goal_id",
        UUID(as_uuid=True),
        ForeignKey("poc_goals.id", ondelete="CASCADE"),
        nullable=False,
    )

    discipline = Column(
        String(20),
        nullable=False,
    )

    intervention_text = Column(
        Text,
        nullable=False,
    )

    frequency = Column(
        String(100),
        nullable=True,
    )

    instructions = Column(
        Text,
        nullable=True,
    )

    source_kind = Column(
        String(30),
        nullable=False,
        default="RULE_GENERATED",
    )

    is_rule_generated = Column(
        Boolean,
        nullable=False,
        default=True,
    )

    status = Column(
        String(20),
        nullable=False,
        default="ACTIVE",
    )

    sort_order = Column(
        Integer,
        nullable=False,
        default=100,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
    )

    created_by_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        onupdate=_utcnow,
    )

    updated_by_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    goal = relationship(
        "POCGoal",
        back_populates="interventions",
        foreign_keys=[goal_id],
    )