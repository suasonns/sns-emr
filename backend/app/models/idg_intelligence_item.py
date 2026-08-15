# models/idg_intelligence_item.py

from __future__ import annotations

import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    String,
    Text,
    UniqueConstraint,
    text,
)

from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.db.base import Base


class IDGIntelligenceItem(Base):
    __tablename__ = "idg_intelligence_items"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    tenant_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    patient_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    benefit_period_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    source_type = Column(
        String(64),
        nullable=False,
        index=True,
    )

    source_table = Column(
        String(128),
        nullable=False,
        index=True,
    )

    source_record_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    source_date = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    source_discipline = Column(
        String(50),
        nullable=True,
    )

    source_author_id = Column(
        UUID(as_uuid=True),
        nullable=True,
    )

    source_author_name = Column(
        String(255),
        nullable=True,
    )

    title = Column(
        String(255),
        nullable=False,
    )

    summary = Column(
        Text,
        nullable=True,
    )

    original_excerpt = Column(
        Text,
        nullable=True,
    )

    category = Column(
        String(100),
        nullable=True,
    )

    severity = Column(
        String(50),
        nullable=True,
    )

    confidence = Column(
        String(50),
        nullable=True,
    )

    requires_idg_discussion = Column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )

    discussion_status = Column(
        String(50),
        nullable=False,
        server_default=text("'PENDING'"),
    )

    idg_review_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    idg_meeting_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    discussed_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    discussed_by = Column(
        UUID(as_uuid=True),
        nullable=True,
    )

    disposition = Column(
        String(50),
        nullable=True,
    )

    idg_summary = Column(
        Text,
        nullable=True,
    )

    # -------------------------------------------------
    # COMMUNICATION HARVEST
    # -------------------------------------------------

    communication_log_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    communication_event_type = Column(
        String(100),
        nullable=True,
    )

    communication_focus_area = Column(
        String(100),
        nullable=True,
    )

    communication_event_time = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    communication_received_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    communication_status = Column(
        String(50),
        nullable=True,
    )

    communication_summary = Column(
        Text,
        nullable=True,
    )

    communication_details = Column(
        JSONB,
        nullable=True,
    )

    reported_by_name = Column(
        String(255),
        nullable=True,
    )

    reported_by_role = Column(
        String(100),
        nullable=True,
    )

    reported_by_discipline = Column(
        String(100),
        nullable=True,
    )

    reported_source_type = Column(
        String(100),
        nullable=True,
    )

    reporting_organization = Column(
        String(255),
        nullable=True,
    )

    received_by_user_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    received_by_name = Column(
        String(255),
        nullable=True,
    )

    received_by_discipline = Column(
        String(100),
        nullable=True,
    )

    # -------------------------------------------------
    # PRIORITY ENGINE CLASSIFICATION
    # -------------------------------------------------

    idg_impact_level = Column(
        String(50),
        nullable=True,
        index=True,
    )

    idg_reason_category = Column(
        String(100),
        nullable=True,
        index=True,
    )

    matched_priority_rule_id = Column(
        UUID(as_uuid=True),
        nullable=True,
    )

    matched_priority_keyword = Column(
        String(255),
        nullable=True,
    )

    clinical_escalation_required = Column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )

    activation_route = Column(
        String(100),
        nullable=True,
    )

    # -------------------------------------------------
    # CLINICAL FLAGS
    # -------------------------------------------------

    is_critical_result = Column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )

    critical_result_summary = Column(
        Text,
        nullable=True,
    )

    harvest_reason = Column(
        Text,
        nullable=True,
    )

    requires_followup = Column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )

    source_priority = Column(
        String(50),
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )

    __table_args__ = (
        UniqueConstraint(
            "source_table",
            "source_record_id",
            name="uq_idg_intelligence_source",
        ),
    )